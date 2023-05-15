# Copyright (c) Microsoft. All rights reserved.

import inspect
from logging import Logger
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.kernel_extensions import KernelExtensions
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.reliability.pass_through_without_retry import (
    PassThroughWithoutRetry,
)
from semantic_kernel.reliability.retry_mechanism import RetryMechanism
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.skill_definition.skill_collection import SkillCollection
from semantic_kernel.skill_definition.skill_collection_base import SkillCollectionBase
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.utils.validation import validate_function_name, validate_skill_name

T = TypeVar("T")


class Kernel(KernelBase, KernelExtensions):
    _log: Logger
    _skill_collection: SkillCollectionBase
    _prompt_template_engine: PromptTemplatingEngine
    _memory: SemanticTextMemoryBase

    def __init__(
        self,
        skill_collection: Optional[SkillCollectionBase] = None,
        prompt_template_engine: Optional[PromptTemplatingEngine] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        log: Optional[Logger] = None,
    ) -> None:
        self._log = log if log else NullLogger()
        self._skill_collection = (
            skill_collection if skill_collection else SkillCollection(self._log)
        )
        self._prompt_template_engine = (
            prompt_template_engine
            if prompt_template_engine
            else PromptTemplateEngine(self._log)
        )
        self._memory = memory if memory else NullMemory()

        self._text_completion_services: Dict[
            str, Callable[["KernelBase"], TextCompletionClientBase]
        ] = {}
        self._chat_services: Dict[
            str, Callable[["KernelBase"], ChatCompletionClientBase]
        ] = {}
        self._text_embedding_generation_services: Dict[
            str, Callable[["KernelBase"], EmbeddingGeneratorBase]
        ] = {}

        self._default_text_completion_service: Optional[str] = None
        self._default_chat_service: Optional[str] = None
        self._default_text_embedding_generation_service: Optional[str] = None

        self._retry_mechanism: RetryMechanism = PassThroughWithoutRetry()

    def kernel(self) -> KernelBase:
        return self

    @property
    def logger(self) -> Logger:
        return self._log

    @property
    def memory(self) -> SemanticTextMemoryBase:
        return self._memory

    @property
    def prompt_template_engine(self) -> PromptTemplatingEngine:
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

        validate_skill_name(skill_name)
        validate_function_name(function_name)

        function = self._create_semantic_function(
            skill_name, function_name, function_config
        )
        self._skill_collection.add_semantic_function(function)

        return function

    async def run_async(
        self,
        *functions: Any,
        input_context: Optional[SKContext] = None,
        input_vars: Optional[ContextVariables] = None,
        input_str: Optional[str] = None,
    ) -> SKContext:
        # if the user passed in a context, prioritize it, but merge with any other inputs
        if input_context is not None:
            context = input_context
            if input_vars is not None:
                context._variables = input_vars.merge_or_overwrite(
                    new_vars=context._variables, overwrite=False
                )

            if input_str is not None:
                context._variables = ContextVariables(input_str).merge_or_overwrite(
                    new_vars=context._variables, overwrite=False
                )

        # if the user did not pass in a context, prioritize an input string, and merge that with input context variables
        else:
            if input_str is not None and input_vars is None:
                variables = ContextVariables(input_str)
            elif input_str is None and input_vars is not None:
                variables = input_vars
            elif input_str is not None and input_vars is not None:
                variables = ContextVariables(input_str)
                variables = variables.merge_or_overwrite(
                    new_vars=input_vars, overwrite=False
                )
            else:
                variables = ContextVariables()
            context = SKContext(
                variables,
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

    def register_memory_store(self, memory_store: MemoryStoreBase) -> None:
        self.use_memory(memory_store)

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
        for _, candidate in inspect.getmembers(skill_instance, inspect.ismethod):
            # If the method is a semantic function, register it
            if not hasattr(candidate, "__sk_function__"):
                continue

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

    def get_ai_service(
        self, type: Type[T], service_id: Optional[str] = None
    ) -> Callable[["KernelBase"], T]:
        matching_type = {}
        if type == TextCompletionClientBase:
            service_id = service_id or self._default_text_completion_service
            matching_type = self._text_completion_services
        elif type == ChatCompletionClientBase:
            service_id = service_id or self._default_chat_service
            matching_type = self._chat_services
        elif type == EmbeddingGeneratorBase:
            service_id = service_id or self._default_text_embedding_generation_service
            matching_type = self._text_embedding_generation_services
        else:
            raise ValueError(f"Unknown AI service type: {type.__name__}")

        if service_id not in matching_type:
            raise ValueError(
                f"{type.__name__} service with service_id '{service_id}' not found"
            )

        return matching_type[service_id]

    def all_text_completion_services(self) -> List[str]:
        return list(self._text_completion_services.keys())

    def all_chat_services(self) -> List[str]:
        return list(self._chat_services.keys())

    def all_text_embedding_generation_services(self) -> List[str]:
        return list(self._text_embedding_generation_services.keys())

    def add_text_completion_service(
        self,
        service_id: str,
        service: Union[
            TextCompletionClientBase, Callable[["KernelBase"], TextCompletionClientBase]
        ],
        overwrite: bool = True,
    ) -> "Kernel":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self._text_completion_services:
            raise ValueError(
                f"Text service with service_id '{service_id}' already exists"
            )

        self._text_completion_services[service_id] = (
            service if isinstance(service, Callable) else lambda _: service
        )
        if self._default_text_completion_service is None:
            self._default_text_completion_service = service_id

        return self

    def add_chat_service(
        self,
        service_id: str,
        service: Union[
            ChatCompletionClientBase, Callable[["KernelBase"], ChatCompletionClientBase]
        ],
        overwrite: bool = True,
    ) -> "Kernel":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self._chat_services:
            raise ValueError(
                f"Chat service with service_id '{service_id}' already exists"
            )

        self._chat_services[service_id] = (
            service if isinstance(service, Callable) else lambda _: service
        )
        if self._default_chat_service is None:
            self._default_chat_service = service_id

        if isinstance(service, TextCompletionClientBase):
            self.add_text_completion_service(service_id, service)
            if self._default_text_completion_service is None:
                self._default_text_completion_service = service_id

        return self

    def add_text_embedding_generation_service(
        self,
        service_id: str,
        service: Union[
            EmbeddingGeneratorBase, Callable[["KernelBase"], EmbeddingGeneratorBase]
        ],
        overwrite: bool = False,
    ) -> "Kernel":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self._text_embedding_generation_services:
            raise ValueError(
                f"Embedding service with service_id '{service_id}' already exists"
            )

        self._text_embedding_generation_services[service_id] = (
            service if isinstance(service, Callable) else lambda _: service
        )
        if self._default_text_embedding_generation_service is None:
            self._default_text_embedding_generation_service = service_id

        return self

    def set_default_text_completion_service(self, service_id: str) -> "Kernel":
        if service_id not in self._text_completion_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        self._default_text_completion_service = service_id
        return self

    def set_default_chat_service(self, service_id: str) -> "Kernel":
        if service_id not in self._chat_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        self._default_chat_service = service_id
        return self

    def set_default_text_embedding_generation_service(
        self, service_id: str
    ) -> "Kernel":
        if service_id not in self._text_embedding_generation_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        self._default_text_embedding_generation_service = service_id
        return self

    def get_text_completion_service_service_id(
        self, service_id: Optional[str] = None
    ) -> str:
        if service_id is None or service_id not in self._text_completion_services:
            if self._default_text_completion_service is None:
                raise ValueError("No default text service is set")
            return self._default_text_completion_service

        return service_id

    def get_chat_service_service_id(self, service_id: Optional[str] = None) -> str:
        if service_id is None or service_id not in self._chat_services:
            if self._default_chat_service is None:
                raise ValueError("No default chat service is set")
            return self._default_chat_service

        return service_id

    def get_text_embedding_generation_service_id(
        self, service_id: Optional[str] = None
    ) -> str:
        if (
            service_id is None
            or service_id not in self._text_embedding_generation_services
        ):
            if self._default_text_embedding_generation_service is None:
                raise ValueError("No default embedding service is set")
            return self._default_text_embedding_generation_service

        return service_id

    def remove_text_completion_service(self, service_id: str) -> "Kernel":
        if service_id not in self._text_completion_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        del self._text_completion_services[service_id]
        if self._default_text_completion_service == service_id:
            self._default_text_completion_service = next(
                iter(self._text_completion_services), None
            )
        return self

    def remove_chat_service(self, service_id: str) -> "Kernel":
        if service_id not in self._chat_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        del self._chat_services[service_id]
        if self._default_chat_service == service_id:
            self._default_chat_service = next(iter(self._chat_services), None)
        return self

    def remove_text_embedding_generation_service(self, service_id: str) -> "Kernel":
        if service_id not in self._text_embedding_generation_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        del self._text_embedding_generation_services[service_id]
        if self._default_text_embedding_generation_service == service_id:
            self._default_text_embedding_generation_service = next(
                iter(self._text_embedding_generation_services), None
            )
        return self

    def clear_all_text_completion_services(self) -> "Kernel":
        self._text_completion_services = {}
        self._default_text_completion_service = None
        return self

    def clear_all_chat_services(self) -> "Kernel":
        self._chat_services = {}
        self._default_chat_service = None
        return self

    def clear_all_text_embedding_generation_services(self) -> "Kernel":
        self._text_embedding_generation_services = {}
        self._default_text_embedding_generation_service = None
        return self

    def clear_all_services(self) -> "Kernel":
        self._text_completion_services = {}
        self._chat_services = {}
        self._text_embedding_generation_services = {}

        self._default_text_completion_service = None
        self._default_chat_service = None
        self._default_text_embedding_generation_service = None

        return self

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

        if function_config.has_chat_prompt:
            service = self.get_ai_service(
                ChatCompletionClientBase,
                function_config.prompt_template_config.default_services[0]
                if len(function_config.prompt_template_config.default_services) > 0
                else None,
            )

            function.set_chat_configuration(
                ChatRequestSettings.from_completion_config(
                    function_config.prompt_template_config.completion
                )
            )

            if service is None:
                raise AIException(
                    AIException.ErrorCodes.InvalidConfiguration,
                    "Could not load chat service, unable to prepare semantic function. "
                    "Function description: "
                    "{function_config.prompt_template_config.description}",
                )

            function.set_chat_service(lambda: service(self))
        else:
            service = self.get_ai_service(
                TextCompletionClientBase,
                function_config.prompt_template_config.default_services[0]
                if len(function_config.prompt_template_config.default_services) > 0
                else None,
            )

            function.set_ai_configuration(
                CompleteRequestSettings.from_completion_config(
                    function_config.prompt_template_config.completion
                )
            )

            if service is None:
                raise AIException(
                    AIException.ErrorCodes.InvalidConfiguration,
                    "Could not load text service, unable to prepare semantic function. "
                    "Function description: "
                    "{function_config.prompt_template_config.description}",
                )

            function.set_ai_service(lambda: service(self))

        return function
