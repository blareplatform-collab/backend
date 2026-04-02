"""
BLARE Signal Model
Standard format for every trading signal BLARE generates.
"""
from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid


@dataclass
class Signal:
    symbol: str
    market: str           # crypto|forex|indices|commodities
    direction: str        # long|short
    timeframe: str
    pattern: str
    entry: float
    stop: float
    target: float
    rr: float = 0.0
    confidence: int = 0
    ai_note: str = ""
    position_size_pct: float = 1.0
    status: str = "pending"
    id: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if self.entry != self.stop:
            self.rr = round(
                abs(self.target - self.entry) / abs(self.entry - self.stop), 2
            )

    def to_dict(self) -> dict:
        return asdict(self)
