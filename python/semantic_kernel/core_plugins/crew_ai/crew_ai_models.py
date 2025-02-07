# Copyright (c) Microsoft. All rights reserved.

from typing import Any


class CrewAIStatusResponse:
    """Represents the status response from Crew AI.

    Attributes:
        state (str): The current state of the Crew AI.
        result (Optional[str]): The result of the last operation, if any.
        last_step (Optional[dict[str, Any]]): Details of the last step performed by the Crew AI, if any.

    Args:
        state (str): The current state of the Crew AI.
        result (Optional[str], optional): The result of the last operation. Defaults to None.
        last_step (Optional[dict[str, Any]], optional): Details of the last step performed by the Crew AI.
        Defaults to None.
    """

    def __init__(self, state: str, result: str | None = None, last_step: dict[str, Any] | None = None):
        """Initialize a new instance of the class.

        Args:
            state (str): The current state of the instance.
            result (Optional[str], optional): The result of the instance. Defaults to None.
            last_step (Optional[dict[str, Any]], optional): The last step information of the instance. Defaults to None.
        """
        self.state = state
        self.result = result
        self.last_step = last_step


class CrewAIKickoffResponse:
    """Represents the kickoff response from Crew AI.

    Attributes:
        kickoff_id (str): The ID of the kickoff response.

    Args:
        kickoff_id (str): The ID of the kickoff response.
    """

    def __init__(self, kickoff_id: str):
        """Initialize a new instance of the class.

        Args:
            kickoff_id (str): The ID of the kickoff response.
        """
        self.kickoff_id = kickoff_id


class CrewAIRequiredInputs:
    """Represents the required inputs for Crew AI.

    Attributes:
        inputs (dict[str, str]): The required inputs for Crew AI.

    Args:
        inputs (dict[str, str]): The required inputs for Crew AI.
    """

    def __init__(self, inputs: dict[str, str]):
        """Initialize a new instance of the class.

        Args:
            inputs (dict[str, str]): The required inputs for Crew AI.
        """
        self.inputs = inputs


class InputMetadata:
    """Represents the metadata for an input required by Crew AI.

    Attributes:
        name (str): The name of the input.
        type (str): The type of the input (e.g., 'string', 'json').
        description (Optional[str]): The description of the input.

    Args:
        name (str): The name of the input.
        type (str): The type of the input.
        description (Optional[str], optional): The description of the input. Defaults to None.
    """

    def __init__(self, name: str, type: str, description: str | None = None):
        """Initialize a new instance of the class.

        Args:
            name (str): The name of the input.
            type (str): The type of the input.
            description (Optional[str], optional): The description of the input. Defaults to None.
        """
        self.name = name
        self.type = type
        self.description = description
