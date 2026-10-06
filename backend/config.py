from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Settings:
    database: Path = ROOT / 'data' / 'soc.db'
    model: Path | None = None
    mode: str = 'replay'
    interface: str | None = None
    token: str = ''
    queue_size: int = 4096
    retention_days: int = 30

    @classmethod
    def from_env(cls):
        return cls(database=Path(os.getenv('IDS_DB', str(ROOT / 'data' / 'soc.db'))).resolve(),
                   model=Path(os.environ['IDS_MODEL']).resolve() if os.getenv('IDS_MODEL') else None,
                   mode=os.getenv('IDS_MODE', 'replay'), interface=os.getenv('IDS_INTERFACE'),
                   token=os.getenv('IDS_TOKEN', ''))

    def validate(self):
        if self.mode not in {'replay', 'live'}:
            raise ValueError('IDS_MODE must be replay or live')
        if self.queue_size < 1 or self.retention_days < 1:
            raise ValueError('Queue size and retention must be positive')
