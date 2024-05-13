from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class SystemStep:
    thought: Optional[str] = None
    action: Optional[str] = None
    action_variables: Optional[Dict[str, str]] = field(default_factory=dict)
    observation: Optional[str] = None
    final_answer: Optional[str] = None
    original_response: Optional[str] = None
