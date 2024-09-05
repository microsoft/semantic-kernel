# Copyright (c) Microsoft. All rights reserved.

import logging
import re
import threading
from collections.abc import Callable
from copy import copy
from typing import Any, ClassVar, Optional

from pydantic import PrivateAttr

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.exceptions import KernelFunctionNotFoundError, KernelInvokeException, KernelPluginNotFoundError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.utils.naming import generate_random_ascii_name

logger: logging.Logger = logging.getLogger(__name__)


class Plan:
    """A plan for the kernel."""

    _state: KernelArguments = PrivateAttr()
    _steps: list["Plan"] = PrivateAttr()
    _function: KernelFunction = PrivateAttr()
    _parameters: KernelArguments = PrivateAttr()
    _outputs: list[str] = PrivateAttr()
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
        """Get the name for the plan."""
        return self._name

    @property
    def state(self) -> KernelArguments:
        """Get the state for the plan."""
        return self._state

    @property
    def steps(self) -> list["Plan"]:
        """Get the steps for the plan."""
        return self._steps

    @property
    def plugin_name(self) -> str:
        """Get the plugin name for the plan."""
        return self._plugin_name

    @property
    def description(self) -> str:
        """Get the description for the plan."""
        return self._description

    @property
    def function(self) -> Callable[..., Any]:
        """Get the function for the plan."""
        return self._function

    @property
    def parameters(self) -> KernelArguments:
        """Get the parameters for the plan."""
        return self._parameters

    @property
    def is_prompt(self) -> bool:
        """Check if the plan is a prompt."""
        return self._is_prompt

    @property
    def is_native(self) -> bool:
        """Check if the plan is native code."""
        if self._is_prompt is None:
            return None
        return not self._is_prompt

    @property
    def prompt_execution_settings(self) -> PromptExecutionSettings:
        """Get the AI configuration for the plan."""
        return self._prompt_execution_settings

    @property
    def has_next_step(self) -> bool:
        """Check if the plan has a next step."""
        return self._next_step_index < len(self._steps)

    @property
    def next_step_index(self) -> int:
        """Get the next step index."""
        return self._next_step_index

    def __init__(
        self,
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
        self._plugin_name = f"p_{generate_random_ascii_name()}" if plugin_name is None else plugin_name
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
        """Create a plan from a goal."""
        return cls(description=goal, plugin_name=cls.__name__)

    @classmethod
    def from_function(cls, function: KernelFunction) -> "Plan":
        """Create a plan from a function."""
        plan = cls()
        plan.set_function(function)
        return plan

    async def invoke(
        self,
        kernel: Kernel,
        arguments: KernelArguments | None = None,
    ) -> FunctionResult:
        """Invoke the plan asynchronously.

        Args:
            kernel (Kernel): The kernel to use for invocation.
            arguments (KernelArguments, optional): The context to use. Defaults to None.

        Returns:
            FunctionResult: The result of the function.
        """
        if not arguments:
            arguments = copy(self._state)
        if self._function is not None:
            try:
                result = await self._function.invoke(kernel=kernel, arguments=arguments)
            except Exception as exc:
                logger.error(f"Something went wrong in plan step {self._plugin_name}.{self._name}:'{exc}'")
                raise KernelInvokeException(
                    "Error occurred while running plan step: " + str(exc),
                    exc,
                ) from exc
            return result
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

        return FunctionResult(function=self.metadata, value=result_string, metadata={"results": partial_results})

    def set_ai_configuration(
        self,
        settings: PromptExecutionSettings,
    ) -> None:
        """Set the AI configuration for the plan."""
        self._prompt_execution_settings = settings

    @property
    def metadata(self) -> KernelFunctionMetadata:
        """Get the metadata for the plan."""
        if self._function is not None:
            return self._function.metadata
        return KernelFunctionMetadata(
            name=self._name or "Plan",
            plugin_name=self._plugin_name,
            parameters=[],
            description=self._description,
            is_prompt=self._is_prompt or False,
        )

    def set_available_functions(self, plan: "Plan", kernel: "Kernel", arguments: "KernelArguments") -> "Plan":
        """Set the available functions for the plan."""
        if len(plan.steps) == 0:
            try:
                plugin_function = kernel.get_function(plan.plugin_name, plan.name)
                plan.set_function(plugin_function)
            except (KernelFunctionNotFoundError, KernelPluginNotFoundError) as exc:
                logger.error(
                    f"Something went wrong when setting available functions in {self._plugin_name}.{self._name}:'{exc}'"
                )
                pass
        else:
            for step in plan.steps:
                step = self.set_available_functions(step, kernel, arguments)

        return plan

    def add_steps(self, steps: list["Plan"] | list[KernelFunction]) -> None:
        """Add steps to the plan."""
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
        """Set the function for the plan."""
        self._function = function
        self._name = function.name
        self._plugin_name = function.plugin_name
        self._description = function.description
        self._is_prompt = function.is_prompt
        if hasattr(function, "prompt_execution_settings"):
            self._prompt_execution_settings = function.prompt_execution_settings

    async def run_next_step(
        self,
        kernel: Kernel,
        arguments: KernelArguments,
    ) -> Optional["FunctionResult"]:
        """Run the next step in the plan."""
        return await self.invoke_next_step(kernel, arguments)

    async def invoke_next_step(self, kernel: Kernel, arguments: KernelArguments) -> Optional["FunctionResult"]:
        """Invoke the next step in the plan."""
        if not self.has_next_step:
            return None
        step = self._steps[self._next_step_index]

        # merge the state with the current context variables for step execution
        arguments = self.get_next_step_arguments(arguments, step)

        try:
            result = await step.invoke(kernel, arguments)
        except Exception as exc:
            raise KernelInvokeException(
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
            self._state[Plan.DEFAULT_RESULT_KEY] = current_plan_result.strip() + str(result)

        # Increment the step
        self._next_step_index += 1
        return result

    def add_variables_to_state(self, state: KernelArguments, variables: KernelArguments) -> None:
        """Add variables to the state."""
        for key in variables:
            if key not in state:
                state[key] = variables[key]

    def update_arguments_with_outputs(self, arguments: KernelArguments) -> KernelArguments:
        """Update the arguments with the outputs from the current step."""
        if Plan.DEFAULT_RESULT_KEY in self._state:
            result_string = self._state[Plan.DEFAULT_RESULT_KEY]
        else:
            result_string = str(self._state)

        arguments["input"] = result_string

        for item in self._steps[self._next_step_index - 1]._outputs:
            arguments[item] = self._state.get(item, result_string)
        return arguments

    def get_next_step_arguments(self, arguments: KernelArguments, step: "Plan") -> KernelArguments:
        """Get the arguments for the next step."""
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
                    self._state[param.name] is not None and self._state[param.name] != ""
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

    def expand_from_arguments(self, arguments: KernelArguments, input_from_step: Any) -> str:
        """Expand variables in the input from the step using the arguments."""
        result = input_from_step
        variables_regex = r"\$(?P<var>\w+)"
        matches = [m for m in re.finditer(variables_regex, str(input_from_step))]
        ordered_matches = sorted(matches, key=lambda m: len(m.group("var")), reverse=True)

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
