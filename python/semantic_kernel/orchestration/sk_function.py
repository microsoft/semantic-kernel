# Copyright (c) Microsoft. All rights reserved.

import asyncio
import platform
import sys
import threading
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING, Any, Callable, List, Optional, cast

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.delegate_handlers import DelegateHandlers
from semantic_kernel.orchestration.delegate_inference import DelegateInference
from semantic_kernel.orchestration.delegate_types import DelegateTypes
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.skill_definition.function_view import FunctionView
from semantic_kernel.skill_definition.parameter_view import ParameterView
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.utils.null_logger import NullLogger

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext

if platform.system() == "Windows" and sys.version_info >= (3, 8, 0):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class SKFunction(SKFunctionBase):
    """
    Semantic Kernel function.
    """

    _parameters: List[ParameterView]
    _delegate_type: DelegateTypes
    _function: Callable[..., Any]
    _skill_collection: Optional[ReadOnlySkillCollectionBase]
    _log: Logger
    _ai_service: Optional[TextCompletionClientBase]
    _ai_request_settings: CompleteRequestSettings
    _chat_service: Optional[ChatCompletionClientBase]
    _chat_request_settings: ChatRequestSettings

    @staticmethod
    def from_native_method(method, skill_name="", log=None) -> "SKFunction":
        if method is None:
            raise ValueError("Method cannot be `None`")

        assert method.__sk_function__ is not None, "Method is not a SK function"
        assert method.__sk_function_name__ is not None, "Method name is empty"

        parameters = []
        # sk_function_context_parameters are optionals
        if hasattr(method, "__sk_function_context_parameters__"):
            for param in method.__sk_function_context_parameters__:
                assert "name" in param, "Parameter name is empty"
                assert "description" in param, "Parameter description is empty"
                assert "default_value" in param, "Parameter default value is empty"

                parameters.append(
                    ParameterView(
                        param["name"], param["description"], param["default_value"]
                    )
                )

        if (
            hasattr(method, "__sk_function_input_description__")
            and method.__sk_function_input_description__ is not None
            and method.__sk_function_input_description__ != ""
        ):
            input_param = ParameterView(
                "input",
                method.__sk_function_input_description__,
                method.__sk_function_input_default_value__,
            )
            parameters = [input_param] + parameters

        return SKFunction(
            delegate_type=DelegateInference.infer_delegate_type(method),
            delegate_function=method,
            delegate_stream_function=method,
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
        if function_config is None:
            raise ValueError("Function configuration cannot be `None`")

        async def _local_func(client, request_settings, context):
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")

            try:
                if function_config.has_chat_prompt:
                    as_chat_prompt = cast(
                        ChatPromptTemplate, function_config.prompt_template
                    )

                    # Similar to non-chat, render prompt (which renders to a
                    # list of <role, content> messages)
                    messages = await as_chat_prompt.render_messages_async(context)
                    completion = await client.complete_chat_async(
                        messages, request_settings
                    )

                    # Add the last message from the rendered chat prompt
                    # (which will be the user message) and the response
                    # from the model (the assistant message)
                    _, content = messages[-1]
                    as_chat_prompt.add_user_message(content)
                    as_chat_prompt.add_assistant_message(completion)

                    # Update context
                    context.variables.update(completion)
                else:
                    prompt = await function_config.prompt_template.render_async(context)
                    completion = await client.complete_async(prompt, request_settings)
                    context.variables.update(completion)
            except Exception as e:
                # TODO: "critical exceptions"
                context.fail(str(e), e)

            return context

        async def _local_stream_func(client, request_settings, context):
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")

            try:
                if function_config.has_chat_prompt:
                    as_chat_prompt = cast(
                        ChatPromptTemplate, function_config.prompt_template
                    )

                    # Similar to non-chat, render prompt (which renders to a
                    # list of <role, content> messages)
                    completion = ""
                    messages = await as_chat_prompt.render_messages_async(context)
                    async for steam_message in client.complete_chat_stream_async(
                        messages, request_settings
                    ):
                        completion += steam_message
                        yield steam_message

                    # Add the last message from the rendered chat prompt
                    # (which will be the user message) and the response
                    # from the model (the assistant message)
                    _, content = messages[-1]
                    as_chat_prompt.add_user_message(content)
                    as_chat_prompt.add_assistant_message(completion)

                    # Update context
                    context.variables.update(completion)
                else:
                    prompt = await function_config.prompt_template.render_async(context)

                    completion = ""
                    async for stream_message in client.complete_stream_async(
                        prompt, request_settings
                    ):
                        completion += stream_message
                        yield stream_message
                    context.variables.update(completion)
            except Exception as e:
                # TODO: "critical exceptions"
                context.fail(str(e), e)

        return SKFunction(
            delegate_type=DelegateTypes.ContextSwitchInSKContextOutTaskSKContext,
            delegate_function=_local_func,
            delegate_stream_function=_local_stream_func,
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
        delegate_stream_function: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._delegate_type = delegate_type
        self._function = delegate_function
        self._parameters = parameters
        self._description = description
        self._skill_name = skill_name
        self._name = function_name
        self._is_semantic = is_semantic
        self._log = log if log is not None else NullLogger()
        self._stream_function = delegate_stream_function
        self._skill_collection = None
        self._ai_service = None
        self._ai_request_settings = CompleteRequestSettings()
        self._chat_service = None
        self._chat_request_settings = ChatRequestSettings()

    def set_default_skill_collection(
        self, skills: ReadOnlySkillCollectionBase
    ) -> "SKFunction":
        self._skill_collection = skills
        return self

    def set_ai_service(
        self, ai_service: Callable[[], TextCompletionClientBase]
    ) -> "SKFunction":
        if ai_service is None:
            raise ValueError("AI LLM service factory cannot be `None`")
        self._verify_is_semantic()
        self._ai_service = ai_service()
        return self

    def set_chat_service(
        self, chat_service: Callable[[], ChatCompletionClientBase]
    ) -> "SKFunction":
        if chat_service is None:
            raise ValueError("Chat LLM service factory cannot be `None`")
        self._verify_is_semantic()
        self._chat_service = chat_service()
        return self

    def set_ai_configuration(self, settings: CompleteRequestSettings) -> "SKFunction":
        if settings is None:
            raise ValueError("AI LLM request settings cannot be `None`")
        self._verify_is_semantic()
        self._ai_request_settings = settings
        return self

    def set_chat_configuration(self, settings: ChatRequestSettings) -> "SKFunction":
        if settings is None:
            raise ValueError("Chat LLM request settings cannot be `None`")
        self._verify_is_semantic()
        self._chat_request_settings = settings
        return self

    def describe(self) -> FunctionView:
        return FunctionView(
            name=self.name,
            skill_name=self.skill_name,
            description=self.description,
            is_semantic=self.is_semantic,
            parameters=self._parameters,
        )

    def __call__(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[CompleteRequestSettings] = None,
        log: Optional[Logger] = None,
    ) -> "SKContext":
        return self.invoke(
            input=input,
            variables=variables,
            context=context,
            memory=memory,
            settings=settings,
            log=log,
        )

    def invoke(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[CompleteRequestSettings] = None,
        log: Optional[Logger] = None,
    ) -> "SKContext":
        from semantic_kernel.orchestration.sk_context import SKContext

        if context is None:
            context = SKContext(
                variables=ContextVariables("") if variables is None else variables,
                skill_collection=self._skill_collection,
                memory=memory if memory is not None else NullMemory.instance,
                logger=log if log is not None else self._log,
            )
        else:
            # If context is passed, we need to merge the variables
            if variables is not None:
                context.variables = variables.merge_or_overwrite(
                    new_vars=context.variables, overwrite=False
                )
            if memory is not None:
                context.memory = memory

        if input is not None:
            context.variables.update(input)

        # Check if there is an event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        # Handle "asyncio.run() cannot be called from a running event loop"
        if loop and loop.is_running():
            if self.is_semantic:
                return self._runThread(self._invoke_semantic_async(context, settings))
            else:
                return self._runThread(self._invoke_native_async(context))
        else:
            if self.is_semantic:
                return asyncio.run(self._invoke_semantic_async(context, settings))
            else:
                return asyncio.run(self._invoke_native_async(context))

    async def invoke_async(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[CompleteRequestSettings] = None,
        log: Optional[Logger] = None,
    ) -> "SKContext":
        from semantic_kernel.orchestration.sk_context import SKContext

        if context is None:
            context = SKContext(
                variables=ContextVariables("") if variables is None else variables,
                skill_collection=self._skill_collection,
                memory=memory if memory is not None else NullMemory.instance,
                logger=log if log is not None else self._log,
            )
        else:
            # If context is passed, we need to merge the variables
            if variables is not None:
                context.variables = variables.merge_or_overwrite(
                    new_vars=context.variables, overwrite=False
                )
            if memory is not None:
                context.memory = memory

        if input is not None:
            context.variables.update(input)

        try:
            if self.is_semantic:
                return await self._invoke_semantic_async(context, settings)
            else:
                return await self._invoke_native_async(context)
        except Exception as e:
            context.fail(str(e), e)
            return context

    async def _invoke_semantic_async(self, context, settings):
        self._verify_is_semantic()

        self._ensure_context_has_skills(context)

        if settings is None:
            if self._ai_service is not None:
                settings = self._ai_request_settings
            elif self._chat_service is not None:
                settings = self._chat_request_settings
            else:
                raise KernelException(
                    KernelException.ErrorCodes.UnknownError,
                    "Semantic functions must have either an AI service or Chat service",
                )

        service = (
            self._ai_service if self._ai_service is not None else self._chat_service
        )
        new_context = await self._function(service, settings, context)
        context.variables.merge_or_overwrite(new_context.variables)
        return context

    async def _invoke_native_async(self, context):
        self._verify_is_native()

        self._ensure_context_has_skills(context)

        delegate = DelegateHandlers.get_handler(self._delegate_type)
        # for python3.9 compatibility (staticmethod is not callable)
        if not hasattr(delegate, "__call__"):
            delegate = delegate.__func__
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

    async def invoke_stream_async(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[CompleteRequestSettings] = None,
        log: Optional[Logger] = None,
    ):
        from semantic_kernel.orchestration.sk_context import SKContext

        if context is None:
            context = SKContext(
                variables=ContextVariables("") if variables is None else variables,
                skill_collection=self._skill_collection,
                memory=memory if memory is not None else NullMemory.instance,
                logger=log if log is not None else self._log,
            )
        else:
            # If context is passed, we need to merge the variables
            if variables is not None:
                context.variables = variables.merge_or_overwrite(
                    new_vars=context.variables, overwrite=False
                )
            if memory is not None:
                context._memory = memory

        if input is not None:
            context.variables.update(input)

        try:
            if self.is_semantic:
                async for stream_msg in self._invoke_semantic_stream_async(
                    context, settings
                ):
                    yield stream_msg
            else:
                async for stream_msg in self._invoke_native_stream_async(context):
                    yield stream_msg
        except Exception as e:
            context.fail(str(e), e)
            raise KernelException(
                KernelException.ErrorCodes.FunctionInvokeError,
                "Error occurred while invoking stream function",
            )

    async def _invoke_semantic_stream_async(self, context, settings):
        self._verify_is_semantic()

        self._ensure_context_has_skills(context)

        if settings is None:
            if self._ai_service is not None:
                settings = self._ai_request_settings
            elif self._chat_service is not None:
                settings = self._chat_request_settings
            else:
                raise KernelException(
                    KernelException.ErrorCodes.UnknownError,
                    "Semantic functions must have either an AI service or Chat service",
                )

        service = (
            self._ai_service if self._ai_service is not None else self._chat_service
        )

        async for stream_msg in self._stream_function(service, settings, context):
            yield stream_msg

    async def _invoke_native_stream_async(self, context):
        result = await self._invoke_native_async(context)

        yield result

    def _ensure_context_has_skills(self, context) -> None:
        if context.skills is not None:
            return

        context.skills = self._skill_collection

    def _trace_function_type_Call(self, type: Enum, log: Logger) -> None:
        log.debug(f"Executing function type {type}: {type.name}")

    """
    Async code wrapper to allow running async code inside external
    event loops such as Jupyter notebooks.
    """

    def _runThread(self, code: Callable):
        result = []
        thread = threading.Thread(target=self._runCode, args=(code, result))
        thread.start()
        thread.join()
        return result[0]

    def _runCode(self, code: Callable, result: List[Any]) -> None:
        result.append(asyncio.run(code))
