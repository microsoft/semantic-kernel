import json
import regex
from typing import Any, List, Union, Optional
from logging import Logger
from semantic_kernel import Kernel
from python.semantic_kernel.kernel_exception import KernelException
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.connectors.ai import CompleteRequestSettings
from python.semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase

from python.semantic_kernel.skill_definition.function_view import FunctionView
from python.semantic_kernel.skill_definition.parameter_view import ParameterView


class Plan(SKFunctionBase):
    state: ContextVariables
    steps: List["Plan"]
    parameters: ContextVariables
    outputs: List[str]
    has_next_step: bool
    next_step_index: int
    name: str
    skill_name: str
    description: str
    is_semantic: bool
    is_sensitive: bool
    trust_service_instance: bool
    request_settings: CompleteRequestSettings
    DEFAULT_RESULT_KEY = "PLAN.RESULT"

    @property
    def name(self) -> str:
        return self._name

    @property
    def skill_name(self) -> str:
        return self._skill_name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> List[ParameterView]:
        return self._parameters

    @property
    def is_semantic(self) -> bool:
        return self._is_semantic

    @property
    def is_native(self) -> bool:
        return not self._is_semantic

    @property
    def request_settings(self) -> CompleteRequestSettings:
        return self._ai_request_settings
    
    @property
    def is_sensitive(self) -> bool:
        return self._is_sensitive
    
    @property
    def trust_service_instance(self) -> bool:
        return self._trust_service_instance
    
    @property
    def has_next_step(self) -> bool:
        return self.next_step_index < len(self.steps)
    
    @property
    def next_step_index(self) -> int:
        return self._next_step_index

    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
        next_step_index: int,
        state: ContextVariables,
        parameters: ContextVariables,
        outputs: List[str],
        steps: List["Plan"],
    ) -> None:
        self.name = name
        self.skill_name = skill_name
        self.description = description
        self.next_step_index = next_step_index
        self.state = state
        self.parameters = parameters
        self.outputs = outputs
        self.steps = steps


    def describe(self) -> FunctionView:
        return self.function.describe()

    def to_json(self, indented: Optional[bool] = False) -> str:
        return json.dumps(self.__dict__, indent=4 if indented else None)

    def from_json(self, json: Any, context: Optional[SKContext] = None) -> "Plan":
        # Filter out good JSON from the input in case additional text is present
        json_regex = r"\{(?:[^{}]|(?R))*\}"
        plan_string = regex.search(json_regex, json).group()
        new_plan = Plan() ## TODO: Fix this
        new_plan.__dict__ = json.loads(plan_string)

        if context is None:
            new_plan = self.set_available_functions(new_plan, context)

        return new_plan
    
    def set_available_functions(self, plan: "Plan", context: SKContext) -> "Plan":
        if len(plan.steps) == 0:
            if context.skills is None:
                raise KernelException(
                    KernelException.ErrorCodes.SkillCollectionNotSet,
                    "Skill collection not found in the context")
            try:
                skillFunction = context.skills.get_function(plan.skill_name, plan.name)
                plan.set_function(skillFunction)
            except:
                pass
        else:
            for step in plan.steps:
                step = self.set_available_functions(step, context)

        return plan
    
    def add_steps(self, steps: Optional[List[SKFunctionBase]]) -> None:
        for step in steps:
            if type(step) is Plan:
                self.steps.append(step)
            else:
                new_step = Plan(
                    step.name,
                    step.skill_name,
                    step.description,
                    0,
                    ContextVariables(),
                    ContextVariables(),
                    [],
                    [],
                )
                new_step.set_function(step)
                self.steps.append(new_step)

    def set_function(self, function: SKFunctionBase) -> None:
        self.function = function
        self.name = function.name
        self.skill_name = function.skill_name
        self.description = function.description
        self.is_semantic = function.is_semantic
        self.is_sensitive = function.is_sensitive
        self.trust_service_instance = function.trust_service_instance
        self.request_settings = function.request_settings
    
    def run_next_step_async(
        self,
        kernel: Kernel,
        variables: ContextVariables,
    ) -> "Plan":
        context = kernel.create_new_context(variables)
        return self.invoke_next_step(context)

    async def invoke_next_step(self, context: SKContext) -> "Plan":
        if self.has_next_step:
            step = self.steps[self.next_step_index]

            # merge the state with the current context variables for step execution
            variables = self.get_next_step_variables(context.variables, step)

            # Invoke the step
            func_context = SKContext(
                variables=variables,
                memory=context._memory,
                skills=context.skills,
                logger=context.logger
            )
            result = await step.invoke_async(func_context)
            result_value = result.result.strip()

            if result.error_occurred:
                raise KernelException(
                    KernelException.ErrorCodes.FunctionInvokeError,
                    "Error occured while running plan step: " + result.last_error_description,
                    result.last_exception
                )
            
            # Update state with result
            self.state.update(result_value)

            # Update plan result in state with matching outputs (if any)
            if self.outputs.intersect(step.outputs).any():                
                current_plan_result = ""
                if Plan.DEFAULT_RESULT_KEY in self.state:
                    current_plan_result = self.state[Plan.DEFAULT_RESULT_KEY]
                self.state.set(Plan.DEFAULT_RESULT_KEY, current_plan_result.strip() + result_value)


            # Update state with outputs (if any)
            for output in step.outputs:
                if output in result.variables:
                    self.state.set(output, result.variables[output])
                else:
                    self.state.set(output, result_value)

            # Increment the step
            self.next_step_index += 1

        return self
    
    async def invoke_async(
        self,
        context: SKContext,
        input: Optional[str] = None,
        settings: Optional[CompleteRequestSettings] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        logger: Optional[Logger] = None,
        # TODO: cancellation_token: CancellationToken,
    ) -> SKContext:
        if input is not None:
            self.state.update(input)
        
        context = SKContext(
            variables=self.state,
            memory=memory,
            logger=logger
        )
        
        if self.function is not None:
            result = await self.function.invoke_async(context=context, settings=settings)
            if result.error_occurred:
                result.log.error(
                    msg="Something went wrong in plan step {0}.{1}:'{2}'".format(
                        self.skill_name,
                        self.name,
                        context.last_error_description
                    )
                )
                return result
            
            context.variables.update(result.result)
        else:
            # loop through steps until completion
            while self.has_next_step:
                function_context = context
                self.add_variables_to_context(self.state, function_context)
                await self.invoke_next_step(function_context)
                self.update_context_with_outputs(context)

        return context

    def add_variables_to_context(
        self,
        variables: ContextVariables,
        context: SKContext
    ) -> None:
        for key in variables.keys():
            if not context.variables.contains_key(key):
                context.variables.set(key, variables[key])

    def update_context_with_outputs(self, context: SKContext) -> None:
        result_string = ""
        if Plan.DEFAULT_RESULT_KEY in self.state:
            result_string = self.state[Plan.DEFAULT_RESULT_KEY]
        else:
            result_string = str(self.state)

        context.variables.update(result_string)

        for item in self.steps[self.next_step_index-1].outputs:
            if item in self.state:
                context.variables.set(item, self.state[item])
            else:
                context.variables.set(item, result_string)

        return context