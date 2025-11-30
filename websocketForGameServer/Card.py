from dataclasses import dataclass

@dataclass
class Card:
    value: int
    color: str
    operator: str