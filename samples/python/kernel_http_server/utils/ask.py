from dataclasses import dataclass
from dataclasses_json import dataclass_json

from typing import List


@dataclass_json
@dataclass
class AskInput:
    key: str = None
    value: str = None


@dataclass_json
@dataclass
class Ask:
    skills: List[str] = None
    inputs: List[AskInput] = None
    value: str = None


@dataclass_json
@dataclass
class AskResult:
    value: str = None
    state: List[AskInput] = None
