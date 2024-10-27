# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Mapping
from typing import TYPE_CHECKING, Any, ClassVar
import sys
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from typing import TYPE_CHECKING, Any, ClassVar
from typing import AsyncIterable, List, Optional

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from ollama import AsyncClient
from ollama._types import Message
from ollama._types import Message
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import (
    OllamaChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.ollama.ollama_settings import OllamaSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_base import OllamaBase
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
)
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidResponseError,
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.ollama_settings import OllamaSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_base import OllamaBase
from semantic_kernel.connectors.ai.ollama.services.utils import (
    MESSAGE_CONVERTERS,
    update_settings_from_function_choice_configuration,
)
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion, trace_text_completion
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)
)
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion, trace_text_completion

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent

logger: logging.Logger = logging.getLogger(__name__)


logger: logging.Logger = logging.getLogger(__name__)


class OllamaChatCompletion(
    OllamaBase, TextCompletionClientBase, ChatCompletionClientBase
):
class OllamaChatCompletion(OllamaBase, ChatCompletionClientBase):
    """Initializes a new instance of the OllamaChatCompletion class.
class OllamaChatCompletion(TextCompletionClientBase, ChatCompletionClientBase):
    """
    Initializes a new instance of the OllamaChatCompletion class.
class OllamaChatCompletion(TextCompletionClientBase, ChatCompletionClientBase):
    """
    Initializes a new instance of the OllamaChatCompletion class.

    Make sure to have the ollama service running either locally or remotely.
    """

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    def __init__(
        self,
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False

    def __init__(
        self,
        service_id: str | None = None,
        ai_model_id: str | None = None,
        host: str | None = None,
        client: AsyncClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an OllamaChatCompletion service.

        Args:
            service_id (Optional[str]): Service ID tied to the execution settings. (Optional)
            ai_model_id (Optional[str]): The model name. (Optional)
            host (Optional[str]): URL of the Ollama server, defaults to None and
                will use the default Ollama service address: http://127.0.0.1:11434. (Optional)
            client (Optional[AsyncClient]): A custom Ollama client to use for the service. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to using env vars.
            env_file_encoding (str | None): The encoding of the environment settings file, defaults to 'utf-8'.
        chat_history: ChatHistory,
        settings: OllamaChatPromptExecutionSettings,
    ) -> List[ChatMessageContent]:
        """
        try:
            ollama_settings = OllamaSettings.create(
                model=ai_model_id,
        chat_history: ChatHistory,
        settings: OllamaChatPromptExecutionSettings,
    ) -> List[ChatMessageContent]:
        """
        try:
            ollama_settings = OllamaSettings.create(
                chat_model_id=ai_model_id,
                host=host,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError(
                "Failed to create Ollama settings.", ex
            ) from ex

        if not ollama_settings.model:
            raise ServiceInitializationError("Please provide ai_model_id or OLLAMA_MODEL env variable is required")

        super().__init__(
            service_id=service_id or ollama_settings.model,
            ai_model_id=ollama_settings.model,
            client=client or AsyncClient(host=ollama_settings.host),
        )

        if not ollama_settings.model:
            raise ServiceInitializationError("Please provide ai_model_id or OLLAMA_MODEL env variable is required")
        if not ollama_settings.chat_model_id:
            raise ServiceInitializationError("Ollama chat model ID is required.")

        super().__init__(
            service_id=service_id or ollama_settings.chat_model_id,
            ai_model_id=ollama_settings.chat_model_id,
            client=client or AsyncClient(host=ollama_settings.host),
        )

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return OllamaChatPromptExecutionSettings

    @override
    def _prepare_chat_history_for_request(
        self,
        chat_history: ChatHistory,
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[Message]:
        return [MESSAGE_CONVERTERS[message.role](message) for message in chat_history.messages]

    @override
    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if settings.function_choice_behavior and settings.function_choice_behavior.type_ in [
            FunctionChoiceType.REQUIRED,
            FunctionChoiceType.NONE,
        ]:
            raise ServiceInvalidExecutionSettingsError(
                "Ollama does not support function choice behavior of type 'required' or 'none' yet."
            )

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_choice_configuration

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tools"):
            settings.tools = None

    @override
    @trace_chat_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
    @override
    @trace_chat_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def get_chat_message_contents(
    @trace_chat_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
    @override
    @trace_chat_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, OllamaChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OllamaChatPromptExecutionSettings)  # nosec

        prepared_chat_history = self._prepare_chat_history_for_request(chat_history)

        response_object = await self.client.chat(
            model=self.ai_model_id,
            messages=prepared_chat_history,
            stream=False,
            **settings.prepare_settings_dict(),
        )

        if not isinstance(response_object, Mapping):
            raise ServiceInvalidResponseError(
                "Invalid response type from Ollama chat completion. "
                f"Expected Mapping but got {type(response_object)}."
            )

        return [
            ChatMessageContent(
                inner_content=response_object,
                ai_model_id=self.ai_model_id,
                role=AuthorRole.ASSISTANT,
                content=response_object.get("message", {"content": None}).get(
                    "content", None
                ),
            self._create_chat_message_content(
                response_object,
                self._get_metadata_from_response(response_object),
            )
        ]

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, OllamaChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OllamaChatPromptExecutionSettings)  # nosec

        if settings.tools:
            raise ServiceInvalidExecutionSettingsError(
                "Ollama does not support tool calling in streaming chat completion."
            )

        prepared_chat_history = self._prepare_chat_history_for_request(chat_history)

        response_object = await self.client.chat(
            model=self.ai_model_id,
            messages=prepared_chat_history,
            stream=True,
            **settings.prepare_settings_dict(),
        )

        if not isinstance(response_object, AsyncIterator):
            raise ServiceInvalidResponseError(
                "Invalid response type from Ollama chat completion. "
                f"Expected AsyncIterator but got {type(response_object)}."
            )

        async for part in response_object:
            yield [
                self._create_streaming_chat_message_content(
                    part,
                    self._get_metadata_from_response(part),
                StreamingChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    choice_index=0,
                    inner_content=part,
                    ai_model_id=self.ai_model_id,
                    content=part.get("message", {"content": None}).get("content", None),
                )
            ]

    @override
    @trace_text_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list[TextContent]:
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Args:
            prompt (str): A prompt to complete
            settings (PromptExecutionSettings): Settings for the request.
        Arguments:
            chat_history {ChatHistory} -- A chat history that contains a list of chat messages,
                that can be rendered into a set of messages, from system, user, assistant and function.
            settings {PromptExecutionSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging. (Deprecated)

        Returns:
            List[ChatMessageContent] -- A list of ChatMessageContent objects representing the response(s) from the LLM.
        """
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.stream = False
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                response_object = await response.json()
                return [
                    ChatMessageContent(
                        inner_content=response_object,
                        ai_model_id=self.ai_model_id,
                        role="assistant",
                        content=response_object.get("message", {"content": None}).get("content", None),
                    )
                ]

    async def complete_chat_stream(
        self,
        chat_history: ChatHistory,
        settings: OllamaChatPromptExecutionSettings,
    ) -> AsyncIterable[List[StreamingChatMessageContent]]:
        """
        Streams a text completion using a Ollama model.
        Note that this method does not support multiple responses.

        Arguments:
            chat_history {ChatHistory} -- A chat history that contains a list of chat messages,
                that can be rendered into a set of messages, from system, user, assistant and function.
            settings {OllamaChatPromptExecutionSettings} -- Request settings.

        Yields:
            List[StreamingChatMessageContent] -- Stream of StreamingChatMessageContent objects.
        """
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.stream = True
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                async for line in response.content:
                    body = json.loads(line)
                    if body.get("done") and body.get("message", {}).get("content") is None:
                        break
                    yield [
                        StreamingChatMessageContent(
                            choice_index=0,
                            inner_content=body,
                            ai_model_id=self.ai_model_id,
                            content=body.get("message", {"content": None}).get("content", None),
                        )
                    ]
                    if body.get("done"):
                        break

    async def complete(
        self,
        prompt: str,
        settings: OllamaChatPromptExecutionSettings,
    ) -> List[TextContent]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            chat_history {ChatHistory} -- A chat history that contains the prompt to complete.
            settings {OllamaChatPromptExecutionSettings} -- Settings for the request.

        Returns:
            List["TextContent"]: The completion result(s).
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
        prepared_chat_history = [Message(role=AuthorRole.USER.value, content=prompt)]

        response_object = await self.client.chat(
            model=self.ai_model_id,
            messages=prepared_chat_history,
            stream=False,
            **settings.prepare_settings_dict(),
        )

        if not isinstance(response_object, Mapping):
            raise ServiceInvalidResponseError(
                "Invalid response type from Ollama chat completion. "
                f"Expected Mapping but got {type(response_object)}."
            )

        return [
            TextContent(
                inner_content=response_object,
                ai_model_id=self.ai_model_id,
                text=response_object.get("message", {"content": None}).get(
                    "content", None
                ),
            )
        ]

    async def get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        """Streams a text completion using an Ollama model.

        Note that this method does not support multiple responses.

        Args:
            prompt (str): A chat history that contains the prompt to complete.
            settings (PromptExecutionSettings): Request settings.
        settings: OllamaChatPromptExecutionSettings,
    ) -> AsyncIterable[List[StreamingTextContent]]:
        """
        Streams a text completion using a Ollama model.
        Note that this method does not support multiple responses.

        Arguments:
            prompt {str} -- A chat history that contains the prompt to complete.
            settings {OllamaChatPromptExecutionSettings} -- Request settings.

        Yields:
            List["StreamingTextContent"]: The result stream made up of StreamingTextContent objects.
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
        prepared_chat_history = [Message(role=AuthorRole.USER.value, content=prompt)]

        response_object = await self.client.chat(
            model=self.ai_model_id,
            messages=prepared_chat_history,
            stream=True,
            **settings.prepare_settings_dict(),
        )

        if not isinstance(response_object, AsyncIterator):
            raise ServiceInvalidResponseError(
                "Invalid response type from Ollama chat completion. "
                f"Expected AsyncIterator but got {type(response_object)}."
            )

        async for part in response_object:
            yield [
                StreamingTextContent(
                    choice_index=0,
                    inner_content=part,
                    ai_model_id=self.ai_model_id,
                    text=part.get("message", {"content": None}).get("content", None),
                )
            ]

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return OllamaChatPromptExecutionSettings
    # endregion

    def _create_chat_message_content(self, response: Mapping[str, Any], metadata: dict[str, Any]) -> ChatMessageContent:
        """Create a chat message content from the response."""
        items: list[ITEM_TYPES] = []
        if not (message := response.get("message", None)):
            raise ServiceInvalidResponseError("No message content found in response.")

        if content := message.get("content", None):
            items.append(
                TextContent(
                    text=content,
                    inner_content=message,
                )
            )
        if tool_calls := message.get("tool_calls", None):
            for tool_call in tool_calls:
                items.append(
                    FunctionCallContent(
                        inner_content=tool_call,
                        ai_model_id=self.ai_model_id,
                        name=tool_call.get("function").get("name"),
                        arguments=tool_call.get("function").get("arguments"),
                    )
                )

        return ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=items,
            inner_content=response,
            metadata=metadata,
        )

    def _create_streaming_chat_message_content(
        self, part: Mapping[str, Any], metadata: dict[str, Any]
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content from the response part."""
        items: list[STREAMING_ITEM_TYPES] = []
        if not (message := part.get("message", None)):
            raise ServiceInvalidResponseError("No message content found in response part.")

        if content := message.get("content", None):
            items.append(
                StreamingTextContent(
                    choice_index=0,
                    text=content,
                    inner_content=message,
                )
            )

        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=0,
            items=items,
            inner_content=part,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
        )

    def _get_metadata_from_response(self, response: Mapping[str, Any]) -> dict[str, Any]:
        """Get metadata from the response."""
        metadata = {
            "model": response.get("model"),
        }

        if "prompt_eval_count" in response and "eval_count" in response:
            metadata["usage"] = CompletionUsage(
                prompt_tokens=response.get("prompt_eval_count"),
                completion_tokens=response.get("eval_count"),
            )

        return metadata
