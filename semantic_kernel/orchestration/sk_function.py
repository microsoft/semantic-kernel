# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from logging import Logger
from typing import Any, Callable, List, Optional

from semantic_kernel.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.delegate_handlers import DelegateHandlers
from semantic_kernel.orchestration.delegate_inference import DelegateInference
from semantic_kernel.orchestration.delegate_types import DelegateTypes
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.skill_definition.function_view import FunctionView
from semantic_kernel.skill_definition.parameter_view import ParameterView
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.utils.null_logger import NullLogger


class SKFunction(SKFunctionBase):
    _parameters: List[ParameterView]
    _delegate_type: DelegateTypes
    _function: Callable[..., Any]
    _skill_collection: Optional[ReadOnlySkillCollectionBase]
    _log: Logger
    _ai_backend: Optional[TextCompletionClientBase]
    _ai_request_settings: CompleteRequestSettings

    @staticmethod
    def from_native_method(method, skill_name="", log=None) -> "SKFunction":
        Verify.not_null(method, "Method is empty")

        assert method.__sk_function__ is not None, "Method is not a SK function"
        assert method.__sk_function_name__ is not None, "Method name is empty"

        parameters = []
        for param in method.__sk_function_context_parameters__:
            assert "name" in param, "Parameter name is empty"
            assert "description" in param, "Parameter description is empty"
            assert "default_value" in param, "Parameter default value is empty"

            parameters.append(
                ParameterView(
                    param["name"], param["description"], param["default_value"]
                )
            )

        if hasattr(method, "__sk_function_input_description__"):
            input_param = ParameterView(
                "input",
                method.__sk_function_input_description__,
                method.__sk_function_input_default_value__,
            )
            parameters = [input_param] + parameters

        return SKFunction(
            delegate_type=DelegateInference.infer_delegate_type(method),
            delegate_function=method,
            parameters=parameters,
            description=method.__sk_function_description__,
            skill_name=skill_name,
            function_name=method.__sk_function_name__,
            is_semantic=False,
            log=log,
        )

    @staticmethod
    def from_semantic_config(
        skill_name: str,
        function_name: str,
        function_config: SemanticFunctionConfig,
        log: Optional[Logger] = None,
    ) -> "SKFunction":
        Verify.not_null(function_config, "Function configuration is empty")

        async def _local_func(client, request_settings, context):
            Verify.not_null(client, "AI LLM backend is empty")

            try:
                prompt = await function_config.prompt_template.render_async(context)
                completion = await client.complete_simple_async(
                    prompt, request_settings
                )
                context.variables.update(completion)
            except Exception as e:
                # TODO: "critical exceptions"
                context.fail(str(e), e)

            return context

        return SKFunction(
            delegate_type=DelegateTypes.ContextSwitchInSKContextOutTaskSKContext,
            delegate_function=_local_func,
            parameters=function_config.prompt_template.get_parameters(),
            description=function_config.prompt_template_config.description,
            skill_name=skill_name,
            function_name=function_name,
            is_semantic=True,
            log=log,
        )

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

    def __init__(
        self,
        delegate_type: DelegateTypes,
        delegate_function: Callable[..., Any],
        parameters: List[ParameterView],
        description: str,
        skill_name: str,
        function_name: str,
        is_semantic: bool,
        log: Optional[Logger] = None,
    ) -> None:
        self._delegate_type = delegate_type
        self._function = delegate_function
        self._parameters = parameters
        self._description = description
        self._skill_name = skill_name
        self._name = function_name
        self._is_semantic = is_semantic
        self._log = log if log is not None else NullLogger()
        self._skill_collection = None
        self._ai_backend = None
        self._ai_request_settings = CompleteRequestSettings()

    def set_default_skill_collection(
        self, skills: ReadOnlySkillCollectionBase
    ) -> "SKFunction":
        self._skill_collection = skills
        return self

    def set_ai_backend(
        self, ai_backend: Callable[[], TextCompletionClientBase]
    ) -> "SKFunction":
        Verify.not_null(ai_backend, "AI LLM backend factory is empty")
        self._verify_is_semantic()
        self._ai_backend = ai_backend()
        return self

    def set_ai_configuration(self, settings: CompleteRequestSettings) -> "SKFunction":
        Verify.not_null(settings, "AI LLM request settings are empty")
        self._verify_is_semantic()
        self._ai_request_settings = settings
        return self

    def describe(self) -> FunctionView:
        return FunctionView(
            name=self.name,
            skill_name=self.skill_name,
            description=self.description,
            is_semantic=self.is_semantic,
            parameters=self._parameters,
        )

    async def invoke_async(
        self,
        input: Optional[str] = None,
        context: Optional[SKContext] = None,
        settings: Optional[CompleteRequestSettings] = None,
        log: Optional[Logger] = None,
    ) -> SKContext:
        if context is None:
            Verify.not_null(self._skill_collection, "Skill collection is empty")
            assert self._skill_collection is not None

            context = SKContext(
                ContextVariables(""),
                NullMemory.instance,  # type: ignore
                self._skill_collection,
                log if log is not None else self._log,
                # TODO: ctoken?
            )

        if input is not None:
            context.variables.update(input)

        if self.is_semantic:
            return await self._invoke_semantic_async(context, settings)
        else:
            return await self._invoke_native_async(context)

    async def invoke_with_custom_input_async(
        self,
        input: ContextVariables,
        memory: SemanticTextMemoryBase,
        skills: ReadOnlySkillCollectionBase,
        log: Optional[Logger] = None,
    ) -> SKContext:
        tmp_context = SKContext(
            input,
            memory,
            skills,
            log if log is not None else self._log,
        )

        try:
            return await self.invoke_async(input=None, context=tmp_context, log=log)
        except Exception as e:
            tmp_context.fail(str(e), e)
            return tmp_context

    async def _invoke_semantic_async(self, context, settings):
        self._verify_is_semantic()

        self._ensure_context_has_skills(context)

        if settings is None:
            settings = self._ai_request_settings

        new_context = await self._function(self._ai_backend, settings, context)
        context.variables.merge_or_overwrite(new_context.variables)
        return context

    async def _invoke_native_async(self, context):
        self._verify_is_native()

        self._ensure_context_has_skills(context)

        delegate = DelegateHandlers.get_handler(self._delegate_type)
        new_context = await delegate(self._function, context)

        return new_context

    def _verify_is_semantic(self) -> None:
        if self._is_semantic:
            return

        self._log.error("The function is not semantic")
        raise KernelException(
            KernelException.ErrorCodes.InvalidFunctionType,
            "Invalid operation, the method requires a semantic function",
        )

    def _verify_is_native(self) -> None:
        if not self._is_semantic:
            return

        self._log.error("The function is not native")
        raise KernelException(
            KernelException.ErrorCodes.InvalidFunctionType,
            "Invalid operation, the method requires a native function",
        )

    def _ensure_context_has_skills(self, context) -> None:
        if context.skills is not None:
            return

        context.skills = self._skill_collection

    def _trace_function_type_Call(self, type: Enum, log: Logger) -> None:
        log.debug(f"Executing function type {type}: {type.name}")
