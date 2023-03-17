# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Dict, Optional

from semantic_kernel.ai.ai_exception import AIException
from semantic_kernel.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.ai.open_ai.services.azure_text_completion import (
    AzureTextCompletion,
)
from semantic_kernel.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion,
)
from semantic_kernel.configuration.backend_types import BackendType
from semantic_kernel.configuration.kernel_config import KernelConfig
from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.skill_definition.skill_collection import SkillCollection
from semantic_kernel.skill_definition.skill_collection_base import SkillCollectionBase
from semantic_kernel.template_engine.prompt_template_engine_base import (
    PromptTemplateEngineBase,
)


class Kernel(KernelBase):
    _log: Logger
    _config: KernelConfig
    _skill_collection: SkillCollectionBase
    _prompt_template_engine: PromptTemplateEngineBase
    _memory: SemanticTextMemoryBase

    def __init__(
        self,
        skill_collection: SkillCollectionBase,
        prompt_template_engine: PromptTemplateEngineBase,
        memory: SemanticTextMemoryBase,
        config: KernelConfig,
        log: Logger,
    ) -> None:
        self._log = log
        self._config = config
        self._skill_collection = skill_collection
        self._prompt_template_engine = prompt_template_engine
        self._memory = memory

    @property
    def config(self) -> KernelConfig:
        return self._config

    @property
    def logger(self) -> Logger:
        return self._log

    @property
    def memory(self) -> SemanticTextMemoryBase:
        return self._memory

    @property
    def prompt_template_engine(self) -> PromptTemplateEngineBase:
        return self._prompt_template_engine

    @property
    def skills(self) -> ReadOnlySkillCollectionBase:
        return self._skill_collection.read_only_skill_collection

    def register_semantic_function(
        self,
        skill_name: Optional[str],
        function_name: str,
        function_config: SemanticFunctionConfig,
    ) -> SKFunctionBase:
        if skill_name is None or skill_name == "":
            skill_name = SkillCollection.GLOBAL_SKILL
        assert skill_name is not None  # for type checker

        Verify.valid_skill_name(skill_name)
        Verify.valid_function_name(function_name)

        function = self._create_semantic_function(
            skill_name, function_name, function_config
        )
        self._skill_collection.add_semantic_function(function)

        return function

    async def run_async(self, *functions: Any) -> SKContext:
        return await self.run_on_vars_async(ContextVariables(), *functions)

    async def run_on_str_async(self, input_str: str, *functions: Any) -> SKContext:
        return await self.run_on_vars_async(ContextVariables(input_str), *functions)

    async def run_on_vars_async(
        self, input_vars: ContextVariables, *functions: Any
    ) -> SKContext:
        context = SKContext(
            input_vars,
            self._memory,
            self._skill_collection.read_only_skill_collection,
            self._log,
        )

        pipeline_step = 0
        for func in functions:
            assert isinstance(func, SKFunctionBase), (
                "All func arguments to Kernel.run*(inputs, func1, func2, ...) "
                "must be SKFunctionBase instances"
            )

            if context.error_occurred:
                self._log.error(
                    f"Something went wrong in pipeline step {pipeline_step}. "
                    f"Error description: '{context.last_error_description}'"
                )
                return context

            pipeline_step += 1

            try:
                context = await func.invoke_async(input=None, context=context)

                if context.error_occurred:
                    self._log.error(
                        f"Something went wrong in pipeline step {pipeline_step}. "
                        f"During function invocation: '{func.skill_name}.{func.name}'. "
                        f"Error description: '{context.last_error_description}'"
                    )
                    return context
            except Exception as ex:
                self._log.error(
                    f"Something went wrong in pipeline step {pipeline_step}. "
                    f"During function invocation: '{func.skill_name}.{func.name}'. "
                    f"Error description: '{str(ex)}'"
                )
                context.fail(str(ex), ex)
                return context

        return context

    def func(self, skill_name: str, function_name: str) -> SKFunctionBase:
        if self.skills.has_native_function(skill_name, function_name):
            return self.skills.get_native_function(skill_name, function_name)

        return self.skills.get_semantic_function(skill_name, function_name)

    def register_memory(self, memory: SemanticTextMemoryBase) -> None:
        self._memory = memory

    def create_new_context(self) -> SKContext:
        return SKContext(
            ContextVariables(),
            self._memory,
            self.skills,
            self._log,
        )

    def import_skill(
        self, skill_instance: Any, skill_name: str = ""
    ) -> Dict[str, SKFunctionBase]:
        if skill_name.strip() == "":
            skill_name = SkillCollection.GLOBAL_SKILL
            self._log.debug(f"Importing skill {skill_name} into the global namespace")
        else:
            self._log.debug(f"Importing skill {skill_name}")

        functions = []
        # Read every method from the skill instance
        for candidate in skill_instance.__dict__.values():
            # We're looking for a @staticmethod
            if not isinstance(candidate, staticmethod):
                continue
            candidate = candidate.__func__

            # If the method is a semantic function, register it
            if hasattr(candidate, "__sk_function_name__"):
                functions.append(
                    SKFunction.from_native_method(candidate, skill_name, self.logger)
                )

        self.logger.debug(f"Methods imported: {len(functions)}")

        # Uniqueness check on function names
        function_names = [f.name for f in functions]
        if len(function_names) != len(set(function_names)):
            raise KernelException(
                KernelException.ErrorCodes.FunctionOverloadNotSupported,
                "Overloaded functions are not supported, "
                "please differentiate function names.",
            )

        skill = {}
        for function in functions:
            function.set_default_skill_collection(self.skills)
            self._skill_collection.add_native_function(function)
            skill[function.name] = function

        return skill

    def _create_semantic_function(
        self,
        skill_name: str,
        function_name: str,
        function_config: SemanticFunctionConfig,
    ) -> SKFunctionBase:
        function_type = function_config.prompt_template_config.type
        if not function_type == "completion":
            raise AIException(
                AIException.ErrorCodes.FunctionTypeNotSupported,
                f"Function type not supported: {function_type}",
            )

        function = SKFunction.from_semantic_config(
            skill_name, function_name, function_config
        )
        function.request_settings.update_from_completion_config(
            function_config.prompt_template_config.completion
        )

        # Connect the function to the current kernel skill
        # collection, in case the function is invoked manually
        # without a context and without a way to find other functions.
        function.set_default_skill_collection(self.skills)

        # TODO: allow to postpone this (use lazy init)
        # allow to create semantic functions without
        # a default backend
        backend = self._config.get_completion_backend(
            function_config.prompt_template_config.default_backends[0]
            if len(function_config.prompt_template_config.default_backends) > 0
            else None
        )

        function.set_ai_configuration(
            CompleteRequestSettings.from_completion_config(
                function_config.prompt_template_config.completion
            )
        )

        if backend.backend_type == BackendType.AzureOpenAI:
            Verify.not_null(
                backend.azure_open_ai, "Azure OpenAI configuration is missing"
            )
            function.set_ai_backend(
                lambda: AzureTextCompletion(
                    backend.azure_open_ai.deployment_name,  # type: ignore
                    backend.azure_open_ai.endpoint,  # type: ignore
                    backend.azure_open_ai.api_key,  # type: ignore
                    backend.azure_open_ai.api_version,  # type: ignore
                    self._log,
                )
            )
        elif backend.backend_type == BackendType.OpenAI:
            Verify.not_null(backend.open_ai, "OpenAI configuration is missing")
            function.set_ai_backend(
                lambda: OpenAITextCompletion(
                    backend.open_ai.model_id,  # type: ignore
                    backend.open_ai.api_key,  # type: ignore
                    backend.open_ai.org_id,  # type: ignore
                    self._log,
                )
            )
        else:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                f"Unknown/unsupported backend type: {backend.backend_type.name}, "
                f"unable to prepare semantic function. Function description: "
                f"{function_config.prompt_template_config.description}",
            )

        return function
