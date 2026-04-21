from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class EmissionRecord:
    date: str
    customerId: str
    customerName: str
    assetId: str
    totalKWH: float
    totalCO2: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
