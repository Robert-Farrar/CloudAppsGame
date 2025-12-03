from dataclasses import dataclass
from typing import Optional

@dataclass
class Card:
    value: Optional[int] = None
    color: Optional[str] = None
    operator: Optional[str] = None