# Copyright (c) Microsoft. All rights reserved.

import logging
import re
import threading
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
from collections.abc import Callable
from copy import copy
from typing import Any, ClassVar, Optional
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
from collections.abc import Callable
from copy import copy
from typing import Any, ClassVar, Optional
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
from collections.abc import Callable
from copy import copy
from typing import Any, ClassVar, Optional
=======
from copy import copy
from typing import Any, Callable, ClassVar, List, Optional, Union
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

from pydantic import PrivateAttr

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
from semantic_kernel.exceptions import (
    KernelFunctionNotFoundError,
    KernelInvokeException,
    KernelPluginNotFoundError,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
>>>>>>> Stashed changes
)
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
from semantic_kernel.kernel_exception import KernelException
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
from semantic_kernel.utils.naming import generate_random_ascii_name

logger: logging.Logger = logging.getLogger(__name__)


class Plan:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    """A plan for the kernel."""

    _state: KernelArguments = PrivateAttr()
    _steps: list["Plan"] = PrivateAttr()
    _function: KernelFunction = PrivateAttr()
    _parameters: KernelArguments = PrivateAttr()
    _outputs: list[str] = PrivateAttr()
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
    _state: KernelArguments = PrivateAttr()
    _steps: List["Plan"] = PrivateAttr()
    _function: KernelFunction = PrivateAttr()
    _parameters: KernelArguments = PrivateAttr()
    _outputs: List[str] = PrivateAttr()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    _has_next_step: bool = PrivateAttr()
    _next_step_index: int = PrivateAttr()
    _name: str = PrivateAttr()
    _plugin_name: str = PrivateAttr()
    _description: str = PrivateAttr()
    _is_prompt: bool = PrivateAttr()
    _prompt_execution_settings: PromptExecutionSettings = PrivateAttr()
    DEFAULT_RESULT_KEY: ClassVar[str] = "PLAN.RESULT"

    @property
    def name(self) -> str:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Get the name for the plan."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the name for the plan."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Get the name for the plan."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the name for the plan."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._name

    @property
    def state(self) -> KernelArguments:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
        """Get the state for the plan."""
        return self._state

    @property
    def steps(self) -> list["Plan"]:
        """Get the steps for the plan."""
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
        return self._state

    @property
    def steps(self) -> List["Plan"]:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._steps

    @property
    def plugin_name(self) -> str:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Get the plugin name for the plan."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the plugin name for the plan."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Get the plugin name for the plan."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the plugin name for the plan."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._plugin_name

    @property
    def description(self) -> str:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Get the description for the plan."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the description for the plan."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Get the description for the plan."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the description for the plan."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._description

    @property
    def function(self) -> Callable[..., Any]:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Get the function for the plan."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the function for the plan."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Get the function for the plan."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the function for the plan."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._function

    @property
    def parameters(self) -> KernelArguments:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Get the parameters for the plan."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the parameters for the plan."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Get the parameters for the plan."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the parameters for the plan."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._parameters

    @property
    def is_prompt(self) -> bool:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Check if the plan is a prompt."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Check if the plan is a prompt."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Check if the plan is a prompt."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Check if the plan is a prompt."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._is_prompt

    @property
    def is_native(self) -> bool:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
        """Check if the plan is native code."""
        if self._is_prompt is None:
            return None
        return not self._is_prompt

    @property
    def prompt_execution_settings(self) -> PromptExecutionSettings:
        """Get the AI configuration for the plan."""
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
        if self._is_prompt is None:
            return None
        else:
            return not self._is_prompt

    @property
    def prompt_execution_settings(self) -> PromptExecutionSettings:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._prompt_execution_settings

    @property
    def has_next_step(self) -> bool:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Check if the plan has a next step."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Check if the plan has a next step."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Check if the plan has a next step."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Check if the plan has a next step."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._next_step_index < len(self._steps)

    @property
    def next_step_index(self) -> int:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Get the next step index."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the next step index."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Get the next step index."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Get the next step index."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return self._next_step_index

    def __init__(
        self,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
        name: str | None = None,
        plugin_name: str | None = None,
        description: str | None = None,
        next_step_index: int | None = None,
        state: KernelArguments | None = None,
        parameters: KernelArguments | None = None,
        outputs: list[str] | None = None,
        steps: list["Plan"] | None = None,
        function: KernelFunction | None = None,
    ) -> None:
        """Initializes a new instance of the Plan class."""
        self._name = f"plan_{generate_random_ascii_name()}" if name is None else name
        self._plugin_name = (
            f"p_{generate_random_ascii_name()}" if plugin_name is None else plugin_name
        )
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
        name: Optional[str] = None,
        plugin_name: Optional[str] = None,
        description: Optional[str] = None,
        next_step_index: Optional[int] = None,
        state: Optional[KernelArguments] = None,
        parameters: Optional[KernelArguments] = None,
        outputs: Optional[List[str]] = None,
        steps: Optional[List["Plan"]] = None,
        function: Optional[KernelFunction] = None,
    ) -> None:
        self._name = f"plan_{generate_random_ascii_name()}" if name is None else name
        self._plugin_name = f"p_{generate_random_ascii_name()}" if plugin_name is None else plugin_name
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        self._description = "" if description is None else description
        self._next_step_index = 0 if next_step_index is None else next_step_index
        self._state = KernelArguments() if state is None else state
        self._parameters = KernelArguments() if parameters is None else parameters
        self._outputs = [] if outputs is None else outputs
        self._steps = [] if steps is None else steps
        self._has_next_step = len(self._steps) > 0
        self._is_prompt = None
        self._function = function or None
        self._prompt_execution_settings = None

        if function is not None:
            self.set_function(function)

    @classmethod
    def from_goal(cls, goal: str) -> "Plan":
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Create a plan from a goal."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Create a plan from a goal."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Create a plan from a goal."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Create a plan from a goal."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return cls(description=goal, plugin_name=cls.__name__)

    @classmethod
    def from_function(cls, function: KernelFunction) -> "Plan":
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Create a plan from a function."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Create a plan from a function."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Create a plan from a function."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Create a plan from a function."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        plan = cls()
        plan.set_function(function)
        return plan

    async def invoke(
        self,
        kernel: Kernel,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
        arguments: KernelArguments | None = None,
    ) -> FunctionResult:
        """Invoke the plan asynchronously.

        Args:
            kernel (Kernel): The kernel to use for invocation.
            arguments (KernelArguments, optional): The context to use. Defaults to None.

        Returns:
            FunctionResult: The result of the function.
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
        arguments: Optional[KernelArguments] = None,
        # TODO: cancellation_token: CancellationToken,
    ) -> FunctionResult:
        """
        Invoke the plan asynchronously.

        Args:
            input (str, optional): The input to the plan. Defaults to None.
            context (KernelContext, optional): The context to use. Defaults to None.
            settings (PromptExecutionSettings, optional): The AI request settings to use. Defaults to None.
            memory (SemanticTextMemoryBase, optional): The memory to use. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
<<<<<<< Updated upstream
<<<<<<< HEAD
            KernelContext: The updated context.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            KernelContext: The updated context.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
>>>>>>> Stashed changes
        """
        if not arguments:
            arguments = copy(self._state)
        if self._function is not None:
            try:
                result = await self._function.invoke(kernel=kernel, arguments=arguments)
            except Exception as exc:
                logger.error(
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                    f"Something went wrong in plan step {self._plugin_name}.{self._name}:'{exc}'"
                )
                raise KernelInvokeException(
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                    f"Something went wrong in plan step {self._plugin_name}.{self._name}:'{exc}'"
                )
                raise KernelInvokeException(
=======
<<<<<<< Updated upstream
=======
            KernelContext: The updated context.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
        """
        if not arguments:
            arguments = copy(self._state)
        if self._function is not None:
            try:
                result = await self._function.invoke(kernel=kernel, arguments=arguments)
            except Exception as exc:
                logger.error(
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                    f"Something went wrong in plan step {self._plugin_name}.{self._name}:'{exc}'"
                )
                raise KernelInvokeException(
=======
                    "Something went wrong in plan step {0}.{1}:'{2}'".format(self._plugin_name, self._name, exc)
                )
                raise KernelException(
                    KernelException.ErrorCodes.FunctionInvokeError,
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
                    "Error occurred while running plan step: " + str(exc),
                    exc,
                ) from exc
            return result
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
                    "Error occurred while running plan step: " + str(exc),
                    exc,
                ) from exc
            return result
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
        # loop through steps until completion
        partial_results = []
        while self.has_next_step:
            function_arguments = copy(arguments)
            self.add_variables_to_state(self._state, function_arguments)
            logger.info(
                "Invoking next step: "
                + str(self._steps[self._next_step_index].name)
                + " with arguments: "
                + str(function_arguments)
            )
            result = await self.invoke_next_step(kernel, function_arguments)
            if result:
                partial_results.append(result)
                self._state[Plan.DEFAULT_RESULT_KEY] = str(result)
                arguments = self.update_arguments_with_outputs(arguments)
                logger.info(f"updated arguments: {arguments}")

        result_string = str(partial_results[-1]) if len(partial_results) > 0 else ""

        return FunctionResult(
            function=self.metadata,
            value=result_string,
            metadata={"results": partial_results},
        )
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
        else:
            # loop through steps until completion
            partial_results = []
            while self.has_next_step:
                function_arguments = copy(arguments)
                self.add_variables_to_state(self._state, function_arguments)
                logger.error(
                    "Invoking next step: "
                    + str(self._steps[self._next_step_index].name)
                    + " with arguments: "
                    + str(function_arguments)
                )
                result = await self.invoke_next_step(kernel, function_arguments)
                if result:
                    partial_results.append(result)
                    self._state[Plan.DEFAULT_RESULT_KEY] = str(result)
                    arguments = self.update_arguments_with_outputs(arguments)
                    logger.error(f"updated arguments: {arguments}")

            result_string = str(partial_results[-1]) if len(partial_results) > 0 else ""

            return FunctionResult(function=self.metadata, value=result_string, metadata={"results": partial_results})
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    def set_ai_configuration(
        self,
        settings: PromptExecutionSettings,
    ) -> None:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
        """Set the AI configuration for the plan."""
        self._prompt_execution_settings = settings

    @property
    def metadata(self) -> KernelFunctionMetadata:
        """Get the metadata for the plan."""
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
        if self._function is not None:
            self._function.set_ai_configuration(settings)

    def set_ai_service(self, service: Callable[[], TextCompletionClientBase]) -> None:
        if self._function is not None:
            self._function.set_ai_service(service)

    @property
    def metadata(self) -> KernelFunctionMetadata:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        if self._function is not None:
            return self._function.metadata
        return KernelFunctionMetadata(
            name=self._name or "Plan",
            plugin_name=self._plugin_name,
            parameters=[],
            description=self._description,
            is_prompt=self._is_prompt or False,
        )

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    def set_available_functions(
        self, plan: "Plan", kernel: "Kernel", arguments: "KernelArguments"
    ) -> "Plan":
        """Set the available functions for the plan."""
        if len(plan.steps) == 0:
            try:
                plugin_function = kernel.get_function(plan.plugin_name, plan.name)
                plan.set_function(plugin_function)
            except (KernelFunctionNotFoundError, KernelPluginNotFoundError) as exc:
                logger.error(
                    f"Something went wrong when setting available functions in {self._plugin_name}.{self._name}:'{exc}'"
                )
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
    def set_available_functions(self, plan: "Plan", kernel: "Kernel", arguments: "KernelArguments") -> "Plan":
        if len(plan.steps) == 0:
            if kernel.plugins is None:
                raise KernelException(
                    KernelException.ErrorCodes.PluginCollectionNotSet,
                    "Plugin collection not found in the context",
                )
            try:
                pluginFunction = kernel.plugins[plan.plugin_name][plan.name]
                plan.set_function(pluginFunction)
            except Exception:
                pass
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        else:
            for step in plan.steps:
                step = self.set_available_functions(step, kernel, arguments)

        return plan

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    def add_steps(self, steps: list["Plan"] | list[KernelFunction]) -> None:
        """Add steps to the plan."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    def add_steps(self, steps: list["Plan"] | list[KernelFunction]) -> None:
        """Add steps to the plan."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    def add_steps(self, steps: list["Plan"] | list[KernelFunction]) -> None:
        """Add steps to the plan."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    def add_steps(self, steps: list["Plan"] | list[KernelFunction]) -> None:
        """Add steps to the plan."""
=======
    def add_steps(self, steps: Union[List["Plan"], List[KernelFunction]]) -> None:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        for step in steps:
            if type(step) is Plan:
                self._steps.append(step)
            else:
                new_step = Plan(
                    name=step.name,
                    plugin_name=step.plugin_name,
                    description=step.description,
                    next_step_index=0,
                    state=KernelArguments(),
                    parameters=KernelArguments(),
                    outputs=[],
                    steps=[],
                )
                new_step.set_function(step)
                self._steps.append(new_step)

    def set_function(self, function: KernelFunction) -> None:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Set the function for the plan."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Set the function for the plan."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        """Set the function for the plan."""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Set the function for the plan."""
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        self._function = function
        self._name = function.name
        self._plugin_name = function.plugin_name
        self._description = function.description
        self._is_prompt = function.is_prompt
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        if hasattr(function, "prompt_execution_settings"):
            self._prompt_execution_settings = function.prompt_execution_settings
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        if hasattr(function, "prompt_execution_settings"):
            self._prompt_execution_settings = function.prompt_execution_settings
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        if hasattr(function, "prompt_execution_settings"):
            self._prompt_execution_settings = function.prompt_execution_settings
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        if hasattr(function, "prompt_execution_settings"):
            self._prompt_execution_settings = function.prompt_execution_settings
=======
        self._prompt_execution_settings = function.prompt_execution_settings
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    async def run_next_step(
        self,
        kernel: Kernel,
        arguments: KernelArguments,
    ) -> Optional["FunctionResult"]:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
        """Run the next step in the plan."""
        return await self.invoke_next_step(kernel, arguments)

    async def invoke_next_step(
        self, kernel: Kernel, arguments: KernelArguments
    ) -> Optional["FunctionResult"]:
        """Invoke the next step in the plan."""
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
        return await self.invoke_next_step(kernel, arguments)

    async def invoke_next_step(self, kernel: Kernel, arguments: KernelArguments) -> Optional["FunctionResult"]:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        if not self.has_next_step:
            return None
        step = self._steps[self._next_step_index]

        # merge the state with the current context variables for step execution
        arguments = self.get_next_step_arguments(arguments, step)

        try:
            result = await step.invoke(kernel, arguments)
        except Exception as exc:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            raise KernelInvokeException(
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            raise KernelInvokeException(
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
            raise KernelInvokeException(
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            raise KernelInvokeException(
=======
            raise KernelException(
                KernelException.ErrorCodes.FunctionInvokeError,
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
                "Error occurred while running plan step: " + str(exc),
                exc,
            ) from exc

        # Update state with result
        self._state["input"] = str(result)

        # Update plan result in state with matching outputs (if any)
        if set(self._outputs).intersection(set(step._outputs)):
            current_plan_result = ""
            if Plan.DEFAULT_RESULT_KEY in self._state:
                current_plan_result = self._state[Plan.DEFAULT_RESULT_KEY]
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            self._state[Plan.DEFAULT_RESULT_KEY] = current_plan_result.strip() + str(
                result
            )
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            self._state[Plan.DEFAULT_RESULT_KEY] = current_plan_result.strip() + str(
                result
            )
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            self._state[Plan.DEFAULT_RESULT_KEY] = current_plan_result.strip() + str(
                result
            )
=======
            self._state[Plan.DEFAULT_RESULT_KEY] = current_plan_result.strip() + str(result)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

        # Increment the step
        self._next_step_index += 1
        return result

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    def add_variables_to_state(
        self, state: KernelArguments, variables: KernelArguments
    ) -> None:
        """Add variables to the state."""
        for key in variables:
            if key not in state:
                state[key] = variables[key]

    def update_arguments_with_outputs(
        self, arguments: KernelArguments
    ) -> KernelArguments:
        """Update the arguments with the outputs from the current step."""
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
    def add_variables_to_state(self, state: KernelArguments, variables: KernelArguments) -> None:
        for key in variables.keys():
            if key not in state.keys():
                state[key] = variables[key]

    def update_arguments_with_outputs(self, arguments: KernelArguments) -> KernelArguments:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        if Plan.DEFAULT_RESULT_KEY in self._state:
            result_string = self._state[Plan.DEFAULT_RESULT_KEY]
        else:
            result_string = str(self._state)

        arguments["input"] = result_string

        for item in self._steps[self._next_step_index - 1]._outputs:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
            arguments[item] = self._state.get(item, result_string)
        return arguments

    def get_next_step_arguments(
        self, arguments: KernelArguments, step: "Plan"
    ) -> KernelArguments:
        """Get the arguments for the next step."""
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
            if item in self._state:
                arguments[item] = self._state[item]
            else:
                arguments[item] = result_string
        return arguments

    def get_next_step_arguments(self, arguments: KernelArguments, step: "Plan") -> KernelArguments:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        # Priority for Input
        # - Parameters (expand from variables if needed)
        # - KernelArguments
        # - Plan.State
        # - Empty if sending to another plan
        # - Plan.Description
        input_ = None
        step_input_value = step._parameters.get("input")
        variables_input_value = arguments.get("input")
        state_input_value = self._state.get("input")
        if step_input_value and step_input_value != "":
            input_ = step_input_value
        elif variables_input_value and variables_input_value != "":
            input_ = variables_input_value
        elif state_input_value and state_input_value != "":
            input_ = state_input_value
        elif len(step._steps) > 0:
            input_ = ""
        elif self._description is not None and self._description != "":
            input_ = self._description

        step_arguments = KernelArguments(input=input_)
        logger.debug(f"Step input: {step_arguments}")

        # Priority for remaining stepVariables is:
        # - Function Parameters (pull from variables or state by a key value)
        # - Step Parameters (pull from variables or state by a key value)
        # - All other variables. These are carried over in case the function wants access to the ambient content.
        function_params = step.metadata
        if function_params:
            logger.debug(f"Function parameters: {function_params.parameters}")
            for param in function_params.parameters:
                if param.name in arguments:
                    step_arguments[param.name] = arguments[param.name]
                elif param.name in self._state and (
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                    self._state[param.name] is not None
                    and self._state[param.name] != ""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                    self._state[param.name] is not None
                    and self._state[param.name] != ""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
                    self._state[param.name] is not None
                    and self._state[param.name] != ""
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                    self._state[param.name] is not None
                    and self._state[param.name] != ""
=======
                    self._state[param.name] is not None and self._state[param.name] != ""
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
                ):
                    step_arguments[param.name] = self._state[param.name]
        logger.debug(f"Added other parameters: {step_arguments}")

        for param_name, param_val in step.parameters.items():
            if param_name in step_arguments:
                continue

            if param_name in arguments:
                step_arguments[param_name] = param_val
            elif param_name in self._state:
                step_arguments[param_name] = self._state[param_name]
            else:
                expanded_value = self.expand_from_arguments(arguments, param_val)
                step_arguments[param_name] = expanded_value

        for item in arguments:
            if item not in step_arguments:
                step_arguments[item] = arguments[item]

        logger.debug(f"Final step arguments: {step_arguments}")

        return step_arguments

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    def expand_from_arguments(
        self, arguments: KernelArguments, input_from_step: Any
    ) -> str:
        """Expand variables in the input from the step using the arguments."""
        result = input_from_step
        variables_regex = r"\$(?P<var>\w+)"
        matches = [m for m in re.finditer(variables_regex, str(input_from_step))]
        ordered_matches = sorted(
            matches, key=lambda m: len(m.group("var")), reverse=True
        )
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
    def expand_from_arguments(self, arguments: KernelArguments, input_from_step: Any) -> str:
        result = input_from_step
        variables_regex = r"\$(?P<var>\w+)"
        matches = [m for m in re.finditer(variables_regex, str(input_from_step))]
        ordered_matches = sorted(matches, key=lambda m: len(m.group("var")), reverse=True)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

        for match in ordered_matches:
            var_name = match.group("var")
            if var_name in arguments:
                result = result.replace(f"${var_name}", arguments[var_name])

        return result

    def _runThread(self, code: Callable):
        result = []
        thread = threading.Thread(target=self._runCode, args=(code, result))
        thread.start()
        thread.join()
        return result[0]
