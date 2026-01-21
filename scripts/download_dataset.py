import argparse
import logging
from pathlib import Path
import zipfile

import pandas as pd
import requests

DEFAULT_URL = "https://www.unb.ca/cic/datasets/IDS-2017/MachineLearningCSV.zip"
CHUNK_SIZE_BYTES = 1024 * 1024


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def download_zip(url: str, destination: Path, force: bool) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        logging.info("Zip already exists at %s", destination)
        return destination

    logging.info("Downloading dataset from %s", url)
    with requests.get(url, stream=True, timeout=(10, 300)) as response:
        response.raise_for_status()
        with destination.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE_BYTES):
                if chunk:
                    file_handle.write(chunk)

    logging.info("Download completed: %s", destination)
    return destination


def extract_zip(zip_path: Path, extract_dir: Path) -> None:
    extract_dir.mkdir(parents=True, exist_ok=True)
    logging.info("Extracting %s to %s", zip_path, extract_dir)
    with zipfile.ZipFile(zip_path, "r") as zip_handle:
        zip_handle.extractall(extract_dir)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [column.strip().replace(" ", "") for column in df.columns]
    label_columns = [column for column in df.columns if column.lower() == "label"]
    if not label_columns:
        raise ValueError("Label column not found in dataset")
    if label_columns[0] != "Label":
        df = df.rename(columns={label_columns[0]: "Label"})
    df["Label"] = df["Label"].astype(str).str.strip()
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    df = df.replace([float("inf"), float("-inf")], pd.NA)
    df = df.dropna()
    return df


def combine_csvs(csv_files: list[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    has_benign = False
    has_attack = False
    write_header = True

    for csv_file in csv_files:
        logging.info("Processing %s", csv_file.name)
        df = pd.read_csv(csv_file, low_memory=False)
        rows_before = len(df)
        df = clean_dataframe(df)
        rows_after = len(df)
        dropped = rows_before - rows_after
        logging.info("Cleaned %s: dropped %s rows", csv_file.name, dropped)

        labels_upper = df["Label"].str.upper()
        has_benign = has_benign or labels_upper.eq("BENIGN").any()
        has_attack = has_attack or labels_upper.ne("BENIGN").any()

        df.to_csv(output_path, mode="w" if write_header else "a", header=write_header, index=False)
        write_header = False

    if not has_benign or not has_attack:
        logging.warning(
            "Label column may not include both benign and attack samples. "
            "Benign present: %s, Attack present: %s",
            has_benign,
            has_attack,
        )


def parse_args(project_root: Path) -> argparse.Namespace:
    default_raw = project_root / "data" / "raw" / "cic-ids2017"
    default_processed = project_root / "data" / "processed"
    parser = argparse.ArgumentParser(description="Download and prepare CIC-IDS2017 dataset")
    parser.add_argument("--url", default=DEFAULT_URL, help="Direct URL to MachineLearningCSV.zip")
    parser.add_argument("--zip-path", type=Path, default=None, help="Path to a pre-downloaded zip")
    parser.add_argument("--raw-dir", type=Path, default=default_raw, help="Where to extract raw data")
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=default_processed,
        help="Where to write the merged dataset",
    )
    parser.add_argument("--force-download", action="store_true", help="Re-download even if zip exists")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    project_root = Path(__file__).resolve().parents[1]
    args = parse_args(project_root)

    raw_dir = args.raw_dir.resolve()
    processed_dir = args.processed_dir.resolve()
    output_csv = processed_dir / "cic-ids2017.csv"

    if args.zip_path:
        zip_path = args.zip_path.resolve()
        if not zip_path.exists():
            raise FileNotFoundError(f"Zip file not found: {zip_path}")
    else:
        zip_path = raw_dir / "MachineLearningCSV.zip"
        try:
            zip_path = download_zip(args.url, zip_path, args.force_download)
        except requests.RequestException as exc:
            logging.error("Download failed: %s", exc)
            logging.error(
                "Manually download MachineLearningCSV.zip and rerun with --zip-path <path>."
            )
            raise

    extract_zip(zip_path, raw_dir)

    csv_files = sorted(raw_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found under {raw_dir}")

    logging.info("Found %s CSV files to merge", len(csv_files))
    combine_csvs(csv_files, output_csv)
    logging.info("Merged dataset saved to %s", output_csv)


if __name__ == "__main__":
    main()
