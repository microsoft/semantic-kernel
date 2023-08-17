# Copyright (c) Microsoft. All rights reserved.

import asyncio
import re
import threading
from logging import Logger
from typing import Any, Callable, List, Optional, Union

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import CompleteRequestSettings
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.skill_definition.function_view import FunctionView
from semantic_kernel.skill_definition.read_only_skill_collection import (
    ReadOnlySkillCollection,
)
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.utils.null_logger import NullLogger


class Plan(SKFunctionBase):
    _state: ContextVariables
    _steps: List["Plan"]
    _function: SKFunctionBase
    _parameters: ContextVariables
    _outputs: List[str]
    _has_next_step: bool
    _next_step_index: int
    _name: str
    _skill_name: str
    _description: str
    _is_semantic: bool
    _request_settings: CompleteRequestSettings
    DEFAULT_RESULT_KEY = "PLAN.RESULT"

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> ContextVariables:
        return self._state

    @property
    def skill_name(self) -> str:
        return self._skill_name

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
    def request_settings(self) -> CompleteRequestSettings:
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
        skill_name: Optional[str] = None,
        description: Optional[str] = None,
        next_step_index: Optional[int] = None,
        state: Optional[ContextVariables] = None,
        parameters: Optional[ContextVariables] = None,
        outputs: Optional[List[str]] = None,
        steps: Optional[List["Plan"]] = None,
        function: Optional[SKFunctionBase] = None,
    ) -> None:
        self._name = "" if name is None else name
        self._skill_name = "" if skill_name is None else skill_name
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
        return cls(description=goal, skill_name=cls.__name__)

    @classmethod
    def from_function(cls, function: SKFunctionBase) -> "Plan":
        plan = cls()
        plan.set_function(function)
        return plan

    async def invoke_async(
        self,
        input: Optional[str] = None,
        context: Optional[SKContext] = None,
        settings: Optional[CompleteRequestSettings] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        logger: Optional[Logger] = None,
        # TODO: cancellation_token: CancellationToken,
    ) -> SKContext:
        if input is not None and input != "":
            self._state.update(input)

        if context is None:
            context = SKContext(
                variables=self._state,
                skill_collection=ReadOnlySkillCollection(),
                memory=memory or NullMemory(),
                logger=logger if logger is not None else NullLogger(),
            )

        if self._function is not None:
            result = await self._function.invoke_async(
                context=context, settings=settings
            )
            if result.error_occurred:
                result.log.error(
                    "Something went wrong in plan step {0}.{1}:'{2}'".format(
                        self._skill_name, self._name, result.last_error_description
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
        settings: Optional[CompleteRequestSettings] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        logger: Optional[Logger] = None,
    ) -> SKContext:
        if input is not None and input != "":
            self._state.update(input)

        if context is None:
            context = SKContext(
                variables=self._state,
                skill_collection=ReadOnlySkillCollection(),
                memory=memory or NullMemory(),
                logger=logger,
            )

        if self._function is not None:
            result = self._function.invoke(context=context, settings=settings)
            if result.error_occurred:
                result.log.error(
                    result.last_exception,
                    "Something went wrong in plan step {0}.{1}:'{2}'".format(
                        self.skill_name, self.name, context.last_error_description
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
        settings: CompleteRequestSettings,
    ) -> SKFunctionBase:
        if self._function is not None:
            self._function.set_ai_configuration(settings)

    def set_ai_service(
        self, service: Callable[[], TextCompletionClientBase]
    ) -> SKFunctionBase:
        if self._function is not None:
            self._function.set_ai_service(service)

    def set_default_skill_collection(
        self,
        skills: ReadOnlySkillCollectionBase,
    ) -> SKFunctionBase:
        if self._function is not None:
            self._function.set_default_skill_collection(skills)

    def describe(self) -> FunctionView:
        return self._function.describe()

    def set_available_functions(self, plan: "Plan", context: SKContext) -> "Plan":
        if len(plan.steps) == 0:
            if context.skills is None:
                raise KernelException(
                    KernelException.ErrorCodes.SkillCollectionNotSet,
                    "Skill collection not found in the context",
                )
            try:
                skillFunction = context.skills.get_function(plan.skill_name, plan.name)
                plan.set_function(skillFunction)
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
                    skill_name=step.skill_name,
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
        self._skill_name = function.skill_name
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
                skill_collection=context.skills,
                logger=context.log,
            )
            result = await step.invoke_async(context=func_context)
            result_value = result.result

            if result.error_occurred:
                raise KernelException(
                    KernelException.ErrorCodes.FunctionInvokeError,
                    "Error occurred while running plan step: "
                    + result.last_error_description,
                    result.last_exception,
                )

            # Update state with result
            self.state.update(result_value)

            # Update plan result in state with matching outputs (if any)
            if set(self._outputs).intersection(set(step._outputs)):
                current_plan_result = ""
                if Plan.DEFAULT_RESULT_KEY in self._state.variables:
                    current_plan_result = self._state[Plan.DEFAULT_RESULT_KEY]
                self._state.set(
                    Plan.DEFAULT_RESULT_KEY, current_plan_result.strip() + result_value
                )

            # Update state with outputs (if any)
            for output in step._outputs:
                if output in result.variables.variables:
                    self._state.set(output, result.variables[output])
                else:
                    self._state.set(output, result_value)

            # Increment the step
            self._next_step_index += 1

        return self

    def add_variables_to_context(
        self, variables: ContextVariables, context: SKContext
    ) -> None:
        for key in variables.variables:
            if not context.variables.contains_key(key):
                context.variables.set(key, variables[key])

    def update_context_with_outputs(self, context: SKContext) -> None:
        result_string = ""
        if Plan.DEFAULT_RESULT_KEY in self._state.variables:
            result_string = self._state[Plan.DEFAULT_RESULT_KEY]
        else:
            result_string = str(self._state)

        context.variables.update(result_string)

        for item in self._steps[self._next_step_index - 1]._outputs:
            if self._state.contains_key(item):
                context.variables.set(item, self._state[item])
            else:
                context.variables.set(item, result_string)

        return context

    def get_next_step_variables(
        self, variables: ContextVariables, step: "Plan"
    ) -> ContextVariables:
        # Priority for Input
        # - Parameters (expand from variables if needed)
        # - SKContext.Variables
        # - Plan.State
        # - Empty if sending to another plan
        # - Plan.Description
        input_string = ""
        step_input_exists, step_input_value = step._parameters.get("input")
        variables_input_exists, variables_input_value = variables.get("input")
        state_input_exists, state_input_value = self._state.get("input")
        if step_input_exists and step_input_value != "":
            input_string = self.expand_from_variables(variables, step_input_value)
        elif variables_input_exists and variables_input_value != "":
            input_string = variables_input_value
        elif state_input_exists and state_input_value != "":
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

            if variables.contains_key(param.name):
                step_variables.set(param.name, variables[param.name])
            elif self._state.contains_key(param.name) and (
                self._state[param.name] is not None and self._state[param.name] != ""
            ):
                step_variables.set(param.name, self._state[param.name])

        for param_var in step.parameters.variables:
            if step_variables.contains_key(param_var):
                continue

            expanded_value = self.expand_from_variables(variables, param_var)
            if expanded_value.lower() == param_var.lower():
                step_variables.set(param_var, step.parameters.variables[param_var])
            elif variables.contains_key(param_var):
                step_variables.set(param_var, variables[param_var])
            elif self._state.contains_key(param_var):
                step_variables.set(param_var, self._state[param_var])
            else:
                step_variables.set(param_var, expanded_value)

        for item in variables.variables:
            if not step_variables.contains_key(item):
                step_variables.set(item, variables[item])

        return step_variables

    def expand_from_variables(
        self, variables: ContextVariables, input_string: str
    ) -> str:
        result = input_string
        variables_regex = r"\$(?P<var>\w+)"
        matches = [m for m in re.finditer(variables_regex, input_string)]
        ordered_matches = sorted(
            matches, key=lambda m: len(m.group("var")), reverse=True
        )

        for match in ordered_matches:
            var_name = match.group("var")
            if variables.contains_key(var_name):
                result = result.replace(f"${var_name}", variables[var_name])

        return result

    def _runThread(self, code: Callable):
        result = []
        thread = threading.Thread(target=self._runCode, args=(code, result))
        thread.start()
        thread.join()
        return result[0]
