# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import re
import threading
from typing import Any, Callable, ClassVar, List, Optional, Union

from pydantic import PrivateAttr

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import AIRequestSettings
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.plugin_definition.function_view import FunctionView
from semantic_kernel.plugin_definition.read_only_plugin_collection import (
    ReadOnlyPluginCollection,
)
from semantic_kernel.plugin_definition.read_only_plugin_collection_base import (
    ReadOnlyPluginCollectionBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class Plan(SKFunctionBase):
    _state: ContextVariables = PrivateAttr()
    _steps: List["Plan"] = PrivateAttr()
    _function: SKFunctionBase = PrivateAttr()
    _parameters: ContextVariables = PrivateAttr()
    _outputs: List[str] = PrivateAttr()
    _has_next_step: bool = PrivateAttr()
    _next_step_index: int = PrivateAttr()
    _name: str = PrivateAttr()
    _plugin_name: str = PrivateAttr()
    _description: str = PrivateAttr()
    _is_semantic: bool = PrivateAttr()
    _request_settings: AIRequestSettings = PrivateAttr()
    DEFAULT_RESULT_KEY: ClassVar[str] = "PLAN.RESULT"

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> ContextVariables:
        return self._state

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @property
    def description(self) -> str:
        return self._description

    @property
    def function(self) -> Callable[..., Any]:
        return self._function

    @property
    def parameters(self) -> ContextVariables:
        return self._parameters

    @property
    def is_semantic(self) -> bool:
        return self._is_semantic

    @property
    def is_native(self) -> bool:
        if self._is_semantic is None:
            return None
        else:
            return not self._is_semantic

    @property
    def request_settings(self) -> AIRequestSettings:
        return self._request_settings

    @property
    def has_next_step(self) -> bool:
        return self._next_step_index < len(self._steps)

    @property
    def next_step_index(self) -> int:
        return self._next_step_index

    def __init__(
        self,
        name: Optional[str] = None,
        plugin_name: Optional[str] = None,
        description: Optional[str] = None,
        next_step_index: Optional[int] = None,
        state: Optional[ContextVariables] = None,
        parameters: Optional[ContextVariables] = None,
        outputs: Optional[List[str]] = None,
        steps: Optional[List["Plan"]] = None,
        function: Optional[SKFunctionBase] = None,
    ) -> None:
        super().__init__()
        self._name = "" if name is None else name
        self._plugin_name = "" if plugin_name is None else plugin_name
        self._description = "" if description is None else description
        self._next_step_index = 0 if next_step_index is None else next_step_index
        self._state = ContextVariables() if state is None else state
        self._parameters = ContextVariables() if parameters is None else parameters
        self._outputs = [] if outputs is None else outputs
        self._steps = [] if steps is None else steps
        self._has_next_step = len(self._steps) > 0
        self._is_semantic = None
        self._function = None if function is None else function
        self._request_settings = None

        if function is not None:
            self.set_function(function)

    @classmethod
    def from_goal(cls, goal: str) -> "Plan":
        return cls(description=goal, plugin_name=cls.__name__)

    @classmethod
    def from_function(cls, function: SKFunctionBase) -> "Plan":
        plan = cls()
        plan.set_function(function)
        return plan

    async def invoke_async(
        self,
        input: Optional[str] = None,
        context: Optional[SKContext] = None,
        settings: Optional[AIRequestSettings] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        **kwargs,
        # TODO: cancellation_token: CancellationToken,
    ) -> SKContext:
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")
        if input is not None and input != "":
            self._state.update(input)

        if context is None:
            context = SKContext(
                variables=self._state,
                plugin_collection=ReadOnlyPluginCollection(),
                memory=memory or NullMemory(),
            )

        if self._function is not None:
            result = await self._function.invoke_async(context=context, settings=settings)
            if result.error_occurred:
                logger.error(
                    "Something went wrong in plan step {0}.{1}:'{2}'".format(
                        self._plugin_name, self._name, result.last_error_description
                    )
                )
                return result
            context.variables.update(result.result)
        else:
            # loop through steps until completion
            while self.has_next_step:
                function_context = context
                self.add_variables_to_context(self._state, function_context)
                await self.invoke_next_step(function_context)
                self.update_context_with_outputs(context)

        return context

    def invoke(
        self,
        input: Optional[str] = None,
        context: Optional[SKContext] = None,
        settings: Optional[AIRequestSettings] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        **kwargs,
    ) -> SKContext:
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")
        if input is not None and input != "":
            self._state.update(input)

        if context is None:
            context = SKContext(
                variables=self._state,
                plugin_collection=ReadOnlyPluginCollection(),
                memory=memory or NullMemory(),
            )

        if self._function is not None:
            result = self._function.invoke(context=context, settings=settings)
            if result.error_occurred:
                logger.error(
                    result.last_exception,
                    "Something went wrong in plan step {0}.{1}:'{2}'".format(
                        self.plugin_name, self.name, context.last_error_description
                    ),
                )
                return result
            context.variables.update(result.result)
        else:
            # loop through steps until completion
            while self.has_next_step:
                # Check if there is an event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                function_context = context
                self.add_variables_to_context(self._state, function_context)

                # Handle "asyncio.run() cannot be called from a running event loop"
                if loop and loop.is_running():
                    self._runThread(self.invoke_next_step(function_context))
                else:
                    asyncio.run(self.invoke_next_step(function_context))
                self.update_context_with_outputs(context)
        return context

    def set_ai_configuration(
        self,
        settings: AIRequestSettings,
    ) -> SKFunctionBase:
        if self._function is not None:
            self._function.set_ai_configuration(settings)

    def set_ai_service(self, service: Callable[[], TextCompletionClientBase]) -> SKFunctionBase:
        if self._function is not None:
            self._function.set_ai_service(service)

    def set_default_plugin_collection(
        self,
        plugins: ReadOnlyPluginCollectionBase,
    ) -> SKFunctionBase:
        if self._function is not None:
            self._function.set_default_plugin_collection(plugins)

    def describe(self) -> Optional[FunctionView]:
        if self._function is not None:
            return self._function.describe()
        return None

    def set_available_functions(self, plan: "Plan", context: SKContext) -> "Plan":
        if len(plan.steps) == 0:
            if context.plugins is None:
                raise KernelException(
                    KernelException.ErrorCodes.PluginCollectionNotSet,
                    "Plugin collection not found in the context",
                )
            try:
                pluginFunction = context.plugins.get_function(plan.plugin_name, plan.name)
                plan.set_function(pluginFunction)
            except Exception:
                pass
        else:
            for step in plan.steps:
                step = self.set_available_functions(step, context)

        return plan

    def add_steps(self, steps: Union[List["Plan"], List[SKFunctionBase]]) -> None:
        for step in steps:
            if type(step) is Plan:
                self._steps.append(step)
            else:
                new_step = Plan(
                    name=step.name,
                    plugin_name=step.plugin_name,
                    description=step.description,
                    next_step_index=0,
                    state=ContextVariables(),
                    parameters=ContextVariables(),
                    outputs=[],
                    steps=[],
                )
                new_step.set_function(step)
                self._steps.append(new_step)

    def set_function(self, function: SKFunctionBase) -> None:
        self._function = function
        self._name = function.name
        self._plugin_name = function.plugin_name
        self._description = function.description
        self._is_semantic = function.is_semantic
        self._request_settings = function.request_settings

    async def run_next_step_async(
        self,
        kernel: Kernel,
        variables: ContextVariables,
    ) -> "Plan":
        context = kernel.create_new_context(variables)
        return await self.invoke_next_step(context)

    async def invoke_next_step(self, context: SKContext) -> "Plan":
        if self.has_next_step:
            step = self._steps[self._next_step_index]

            # merge the state with the current context variables for step execution
            variables = self.get_next_step_variables(context.variables, step)

            # Invoke the step
            func_context = SKContext(
                variables=variables,
                memory=context.memory,
                plugin_collection=context.plugins,
            )
            result = await step.invoke_async(context=func_context)
            result_value = result.result

            if result.error_occurred:
                raise KernelException(
                    KernelException.ErrorCodes.FunctionInvokeError,
                    "Error occurred while running plan step: " + result.last_error_description,
                    result.last_exception,
                )

            # Update state with result
            self.state.update(result_value)

            # Update plan result in state with matching outputs (if any)
            if set(self._outputs).intersection(set(step._outputs)):
                current_plan_result = ""
                if Plan.DEFAULT_RESULT_KEY in self._state.variables:
                    current_plan_result = self._state[Plan.DEFAULT_RESULT_KEY]
                self._state.set(Plan.DEFAULT_RESULT_KEY, current_plan_result.strip() + result_value)

            # Update state with outputs (if any)
            for output in step._outputs:
                if output in result.variables.variables:
                    self._state.set(output, result.variables[output])
                else:
                    self._state.set(output, result_value)

            # Increment the step
            self._next_step_index += 1

        return self

    def add_variables_to_context(self, variables: ContextVariables, context: SKContext) -> None:
        for key in variables.variables:
            if key not in context.variables:
                context.variables.set(key, variables[key])

    def update_context_with_outputs(self, context: SKContext) -> None:
        result_string = ""
        if Plan.DEFAULT_RESULT_KEY in self._state.variables:
            result_string = self._state[Plan.DEFAULT_RESULT_KEY]
        else:
            result_string = str(self._state)

        context.variables.update(result_string)

        for item in self._steps[self._next_step_index - 1]._outputs:
            if item in self._state:
                context.variables.set(item, self._state[item])
            else:
                context.variables.set(item, result_string)

        return context

    def get_next_step_variables(self, variables: ContextVariables, step: "Plan") -> ContextVariables:
        # Priority for Input
        # - Parameters (expand from variables if needed)
        # - SKContext.Variables
        # - Plan.State
        # - Empty if sending to another plan
        # - Plan.Description
        input_string = ""
        step_input_value = step._parameters.get("input")
        variables_input_value = variables.get("input")
        state_input_value = self._state.get("input")
        if step_input_value and step_input_value != "":
            input_string = self.expand_from_variables(variables, step_input_value)
        elif variables_input_value and variables_input_value != "":
            input_string = variables_input_value
        elif state_input_value and state_input_value != "":
            input_string = state_input_value
        elif len(step._steps) > 0:
            input_string = ""
        elif self._description is not None and self._description != "":
            input_string = self._description

        step_variables = ContextVariables(input_string)

        # Priority for remaining stepVariables is:
        # - Function Parameters (pull from variables or state by a key value)
        # - Step Parameters (pull from variables or state by a key value)
        # - All other variables. These are carried over in case the function wants access to the ambient content.
        function_params = step.describe()
        for param in function_params.parameters:
            if param.name.lower() == variables._main_key.lower():
                continue

            if param.name in variables:
                step_variables.set(param.name, variables[param.name])
            elif param.name in self._state and (self._state[param.name] is not None and self._state[param.name] != ""):
                step_variables.set(param.name, self._state[param.name])

        for param_name, param_val in step.parameters.variables.items():
            if param_name in step_variables:
                continue

            if param_name in variables:
                step_variables.set(param_name, param_val)
            elif param_name in self._state:
                step_variables.set(param_name, self._state[param_name])
            else:
                expanded_value = self.expand_from_variables(variables, param_val)
                step_variables.set(param_name, expanded_value)

        for item in variables.variables:
            if item not in step_variables:
                step_variables.set(item, variables[item])

        return step_variables

    def expand_from_variables(self, variables: ContextVariables, input_string: str) -> str:
        result = input_string
        variables_regex = r"\$(?P<var>\w+)"
        matches = [m for m in re.finditer(variables_regex, input_string)]
        ordered_matches = sorted(matches, key=lambda m: len(m.group("var")), reverse=True)

        for match in ordered_matches:
            var_name = match.group("var")
            if var_name in variables:
                result = result.replace(f"${var_name}", variables[var_name])

        return result

    def _runThread(self, code: Callable):
        result = []
        thread = threading.Thread(target=self._runCode, args=(code, result))
        thread.start()
        thread.join()
        return result[0]
