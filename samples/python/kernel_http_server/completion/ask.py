from dataclasses import dataclass
from typing import List


@dataclass
class AskInput:
    key: str = None
    value: str = None


@dataclass
class Ask:
    skills: List[str] = None
    inputs: List[AskInput] = None
    value: str = None


@dataclass
class AskResult:
    value: str = None
    state: List[AskInput] = None
