from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Settings:
    database: Path = ROOT / 'data' / 'soc.db'
    model: Path | None = None
    model_shadow: bool = False
    mode: str = 'replay'
    interface: str | None = None
    token: str = ''
    queue_size: int = 4096
    retention_days: int = 30

    @classmethod
    def from_env(cls):
        bundled = ROOT / 'pretrained/canonical-all-families-v2'
        artifact = Path(os.environ['IDS_MODEL']).resolve() if os.getenv('IDS_MODEL') else bundled if bundled.exists() else None
        default_shadow = '1' if artifact == bundled else '0'
        return cls(database=Path(os.getenv('IDS_DB', str(ROOT / 'data' / 'soc.db'))).resolve(),
                   model=artifact,
                   model_shadow=os.getenv('IDS_MODEL_SHADOW', default_shadow) == '1',
                   mode=os.getenv('IDS_MODE', 'replay'), interface=os.getenv('IDS_INTERFACE'),
                   token=os.getenv('IDS_TOKEN', ''))

    def validate(self):
        if self.mode not in {'replay', 'live'}:
            raise ValueError('IDS_MODE must be replay or live')
        if self.queue_size < 1 or self.retention_days < 1:
            raise ValueError('Queue size and retention must be positive')
