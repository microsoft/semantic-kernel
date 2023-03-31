# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
import json

@dataclass
class Plan:
    # Constants representing the keys used for serializing and deserializing the Plan object
    ID_KEY = "PLAN__ID"
    GOAL_KEY = "PLAN__GOAL"
    PLAN_KEY = "PLAN__PLAN"
    IS_COMPLETE_KEY = "PLAN__ISCOMPLETE"
    IS_SUCCESSFUL_KEY = "PLAN__ISSUCCESSFUL"
    RESULT_KEY = "PLAN__RESULT"

    # Instance variables with default values
    id: str = ''
    goal: str = ''
    plan_string: str = ''
    arguments: str = ''
    is_complete: bool = False
    is_successful: bool = False
    result: str = ''

    def to_json(self) -> str:
        """Converts the Plan object to a JSON string."""
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_string: str) -> 'Plan':
        """Creates a Plan object from a JSON string."""
        kwargs = json.loads(json_string)
        return cls(**kwargs)
