from dataclasses import dataclass


@dataclass
class RiskLevel:
    id: int
    name: str
    min_probability: float
    max_probability: float
    color: str
    suggested_action: str
