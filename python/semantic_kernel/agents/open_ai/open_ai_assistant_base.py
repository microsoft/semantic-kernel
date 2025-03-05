# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
from collections.abc import AsyncIterable, Iterable
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Literal

from openai import AsyncOpenAI
from openai.resources.beta.assistants import Assistant
from openai.resources.beta.threads.messages import Message
from openai.resources.beta.threads.runs.runs import Run
from openai.types.beta.assistant_tool import CodeInterpreterTool, FileSearchTool
from openai.types.beta.threads.runs import RunStep
from pydantic import Field

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel
from semantic_kernel.agents.open_ai.assistant_content_generation import (
    create_chat_message,
    generate_code_interpreter_content,
    generate_function_call_content,
    generate_function_result_content,
    generate_message_content,
    generate_streaming_code_interpreter_content,
    generate_streaming_function_content,
    generate_streaming_message_content,
    get_function_call_contents,
    get_message_contents,
)
from semantic_kernel.agents.open_ai.function_action_result import FunctionActionResult
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.function_calling_utils import (
    kernel_function_metadata_to_function_call_format,
    merge_function_results,
)
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import (
    AgentExecutionException,
    AgentFileNotFoundException,
    AgentInitializationException,
    AgentInvokeException,
)
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import trace_agent_invocation

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.function_call_content import FunctionCallContent
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIAssistantBase(Agent):
    """OpenAI Assistant Base class.

    Manages the interaction with OpenAI Assistants.
    """

    _options_metadata_key: ClassVar[str] = "__run_options"

    ai_model_id: str
    client: AsyncOpenAI
    assistant: Assistant | None = None
    polling_options: RunPollingOptions = Field(default_factory=RunPollingOptions)
    enable_code_interpreter: bool | None = False
    enable_file_search: bool | None = False
    enable_json_response: bool | None = False
    code_interpreter_file_ids: Annotated[list[str] | None, Field(max_length=20)] = Field(default_factory=list)  # type: ignore
    file_search_file_ids: Annotated[
        list[str] | None,
        Field(
            description="There is a limit of 10000 files when using Azure Assistants API, "
            "the OpenAI docs state no limit, hence this is not checked."
        ),
    ] = Field(default_factory=list)  # type: ignore
    temperature: float | None = None
    top_p: float | None = None
    vector_store_id: str | None = None
    metadata: Annotated[dict[str, Any] | None, Field(max_length=20)] = Field(default_factory=dict)  # type: ignore
    max_completion_tokens: int | None = None
    max_prompt_tokens: int | None = None
    parallel_tool_calls_enabled: bool | None = True
    truncation_message_count: int | None = None

    allowed_message_roles: ClassVar[list[str]] = [AuthorRole.USER, AuthorRole.ASSISTANT]
    polling_status: ClassVar[list[str]] = ["queued", "in_progress", "cancelling"]
    error_message_states: ClassVar[list[str]] = ["failed", "cancelled", "expired", "incomplete"]

    channel_type: ClassVar[type[AgentChannel]] = OpenAIAssistantChannel

    _is_deleted: bool = False

    # region Assistant Initialization

    def __init__(
        self,
        ai_model_id: str,
        client: AsyncOpenAI,
        service_id: str,
        *,
        kernel: "Kernel | None" = None,
        id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        enable_code_interpreter: bool | None = None,
        enable_file_search: bool | None = None,
        enable_json_response: bool | None = None,
        code_interpreter_file_ids: list[str] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        vector_store_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAIAssistant Base.

        Args:
            ai_model_id: The AI model id. Defaults to None.
            client: The client, either AsyncOpenAI or AsyncAzureOpenAI.
            service_id: The service id.
            kernel: The kernel. (optional)
            id: The id. Defaults to None. (optional)
            name: The name. Defaults to None. (optional)
            description: The description. Defaults to None. (optional)
            default_headers: The default headers. Defaults to None. (optional)
            instructions: The instructions. Defaults to None. (optional)
            enable_code_interpreter: Enable code interpreter. Defaults to False. (optional)
            enable_file_search: Enable file search. Defaults to False. (optional)
            enable_json_response: Enable JSON response. Defaults to False. (optional)
            code_interpreter_file_ids: The file ids. Defaults to []. (optional)
            temperature: The temperature. Defaults to None. (optional)
            top_p: The top p. Defaults to None. (optional)
            vector_store_id: The vector store id. Defaults to None. (optional)
            metadata: The metadata. Defaults to {}. (optional)
            max_completion_tokens: The max completion tokens. Defaults to None. (optional)
            max_prompt_tokens: The max prompt tokens. Defaults to None. (optional)
            parallel_tool_calls_enabled: Enable parallel tool calls. Defaults to True. (optional)
            truncation_message_count: The truncation message count. Defaults to None. (optional)
            kwargs: The keyword arguments.
        """
        args: dict[str, Any] = {}

        args = {
            "ai_model_id": ai_model_id,
            "client": client,
            "service_id": service_id,
            "instructions": instructions,
            "description": description,
            "enable_code_interpreter": enable_code_interpreter,
            "enable_file_search": enable_file_search,
            "enable_json_response": enable_json_response,
            "code_interpreter_file_ids": code_interpreter_file_ids or [],
            "temperature": temperature,
            "top_p": top_p,
            "vector_store_id": vector_store_id,
            "metadata": metadata or {},
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "parallel_tool_calls_enabled": parallel_tool_calls_enabled,
            "truncation_message_count": truncation_message_count,
        }

        if name is not None:
            args["name"] = name
        if id is not None:
            args["id"] = id
        if kernel is not None:
            args["kernel"] = kernel
        if kwargs:
            args.update(kwargs)

        super().__init__(**args)

    async def create_assistant(
        self,
        ai_model_id: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        name: str | None = None,
        enable_code_interpreter: bool | None = None,
        code_interpreter_file_ids: list[str] | None = None,
        enable_file_search: bool | None = None,
        vector_store_id: str | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> "Assistant":
        """Create the assistant.

        Args:
            ai_model_id: The AI model id. Defaults to None. (optional)
            description: The description. Defaults to None. (optional)
            instructions: The instructions. Defaults to None. (optional)
            name: The name. Defaults to None. (optional)
            enable_code_interpreter: Enable code interpreter. Defaults to None. (optional)
            enable_file_search: Enable file search. Defaults to None. (optional)
            code_interpreter_file_ids: The file ids. Defaults to None. (optional)
            vector_store_id: The vector store id. Defaults to None. (optional)
            metadata: The metadata. Defaults to None. (optional)
            kwargs: Extra keyword arguments.

        Returns:
            Assistant: The assistant
        """
        create_assistant_kwargs: dict[str, Any] = {}

        if ai_model_id is not None:
            create_assistant_kwargs["model"] = ai_model_id
        elif self.ai_model_id:
            create_assistant_kwargs["model"] = self.ai_model_id

        if description is not None:
            create_assistant_kwargs["description"] = description
        elif self.description:
            create_assistant_kwargs["description"] = self.description

        if instructions is not None:
            create_assistant_kwargs["instructions"] = instructions
        elif self.instructions:
            create_assistant_kwargs["instructions"] = self.instructions

        if name is not None:
            create_assistant_kwargs["name"] = name
        elif self.name:
            create_assistant_kwargs["name"] = self.name

        tools = []
        if enable_code_interpreter is not None:
            if enable_code_interpreter:
                tools.append({"type": "code_interpreter"})
        elif self.enable_code_interpreter:
            tools.append({"type": "code_interpreter"})

        if enable_file_search is not None:
            if enable_file_search:
                tools.append({"type": "file_search"})
        elif self.enable_file_search:
            tools.append({"type": "file_search"})

        if tools:
            create_assistant_kwargs["tools"] = tools

        tool_resources = {}
        if code_interpreter_file_ids is not None:
            tool_resources["code_interpreter"] = {"file_ids": code_interpreter_file_ids}
        elif self.code_interpreter_file_ids:
            tool_resources["code_interpreter"] = {"file_ids": self.code_interpreter_file_ids}

        if vector_store_id is not None:
            tool_resources["file_search"] = {"vector_store_ids": [vector_store_id]}
        elif self.vector_store_id:
            tool_resources["file_search"] = {"vector_store_ids": [self.vector_store_id]}

        if tool_resources:
            create_assistant_kwargs["tool_resources"] = tool_resources

        if metadata:
            create_assistant_kwargs["metadata"] = metadata
        elif self.metadata:
            create_assistant_kwargs["metadata"] = self.metadata

        if kwargs:
            create_assistant_kwargs.update(kwargs)

        execution_settings: dict[str, Any] = {}
        if self.max_completion_tokens:
            execution_settings["max_completion_tokens"] = self.max_completion_tokens

        if self.max_prompt_tokens:
            execution_settings["max_prompt_tokens"] = self.max_prompt_tokens

        if self.top_p is not None:
            execution_settings["top_p"] = self.top_p
            create_assistant_kwargs["top_p"] = self.top_p

        if self.temperature is not None:
            execution_settings["temperature"] = self.temperature
            create_assistant_kwargs["temperature"] = self.temperature

        if self.parallel_tool_calls_enabled:
            execution_settings["parallel_tool_calls_enabled"] = self.parallel_tool_calls_enabled

        if self.truncation_message_count:
            execution_settings["truncation_message_count"] = self.truncation_message_count

        if execution_settings:
            if "metadata" not in create_assistant_kwargs:
                create_assistant_kwargs["metadata"] = {}
            if self._options_metadata_key not in create_assistant_kwargs["metadata"]:
                create_assistant_kwargs["metadata"][self._options_metadata_key] = {}
            create_assistant_kwargs["metadata"][self._options_metadata_key] = json.dumps(execution_settings)

        self.assistant = await self.client.beta.assistants.create(
            **create_assistant_kwargs,
        )

        if self._is_deleted:
            self._is_deleted = False

        return self.assistant

    async def modify_assistant(self, assistant_id: str, **kwargs: Any) -> "Assistant":
        """Modify the assistant.

        Args:
            assistant_id: The assistant's current ID.
            kwargs: Extra keyword arguments.

        Returns:
            Assistant: The modified assistant.
        """
        if self.assistant is None:
            raise AgentInitializationException("The assistant has not been created.")

        modified_assistant = await self.client.beta.assistants.update(assistant_id=assistant_id, **kwargs)
        self.assistant = modified_assistant
        return self.assistant

    @classmethod
    def _create_open_ai_assistant_definition(cls, assistant: "Assistant") -> dict[str, Any]:
        """Create an OpenAI Assistant Definition from the provided assistant dictionary.

        Args:
            assistant: The assistant dictionary.

        Returns:
            An OpenAI Assistant Definition.
        """
        execution_settings = {}
        if isinstance(assistant.metadata, dict) and OpenAIAssistantBase._options_metadata_key in assistant.metadata:
            settings_data = assistant.metadata[OpenAIAssistantBase._options_metadata_key]
            if isinstance(settings_data, str):
                settings_data = json.loads(settings_data)
                assistant.metadata[OpenAIAssistantBase._options_metadata_key] = settings_data
            execution_settings = {key: value for key, value in settings_data.items()}

        file_ids: list[str] = []
        vector_store_id = None

        tool_resources = getattr(assistant, "tool_resources", None)
        if tool_resources:
            if hasattr(tool_resources, "code_interpreter") and tool_resources.code_interpreter:
                file_ids = getattr(tool_resources.code_interpreter, "code_interpreter_file_ids", [])

            if hasattr(tool_resources, "file_search") and tool_resources.file_search:
                vector_store_ids = getattr(tool_resources.file_search, "vector_store_ids", [])
                if vector_store_ids:
                    vector_store_id = vector_store_ids[0]

        enable_json_response = (
            hasattr(assistant, "response_format")
            and assistant.response_format is not None
            and getattr(assistant.response_format, "type", "") == "json_object"
        )

        enable_code_interpreter = any(isinstance(tool, CodeInterpreterTool) for tool in assistant.tools)
        enable_file_search = any(isinstance(tool, FileSearchTool) for tool in assistant.tools)

        return {
            "ai_model_id": assistant.model,
            "description": assistant.description,
            "id": assistant.id,
            "instructions": assistant.instructions,
            "name": assistant.name,
            "enable_code_interpreter": enable_code_interpreter,
            "enable_file_search": enable_file_search,
            "enable_json_response": enable_json_response,
            "code_interpreter_file_ids": file_ids,
            "temperature": assistant.temperature,
            "top_p": assistant.top_p,
            "vector_store_id": vector_store_id if vector_store_id else None,
            "metadata": assistant.metadata,
            **execution_settings,
        }

    # endregion

    # region Agent Properties

    @property
    def tools(self) -> list[dict[str, str]]:
        """The tools.

        Returns:
            list[dict[str, str]]: The tools.
        """
        if self.assistant is None:
            raise AgentInitializationException("The assistant has not been created.")
        return self._get_tools()

    # endregion

    # region Agent Channel Methods

    def get_channel_keys(self) -> Iterable[str]:
        """Get the channel keys.

        Returns:
            Iterable[str]: The channel keys.
        """
        # Distinguish from other channel types.
        yield f"{OpenAIAssistantBase.__name__}"

        # Distinguish between different agent IDs
        yield self.id

        # Distinguish between agent names
        yield self.name

        # Distinguish between different API base URLs
        yield str(self.client.base_url)

    async def create_channel(self) -> AgentChannel:
        """Create a channel."""
        thread_id = await self.create_thread()

        return OpenAIAssistantChannel(client=self.client, thread_id=thread_id)

    # endregion

    # region Agent Methods

    async def create_thread(
        self,
        *,
        code_interpreter_file_ids: list[str] | None = [],
        messages: list["ChatMessageContent"] | None = [],
        vector_store_id: str | None = None,
        metadata: dict[str, str] = {},
    ) -> str:
        """Create a thread.

        Args:
            code_interpreter_file_ids: The code interpreter file ids. Defaults to an empty list. (optional)
            messages: The chat messages. Defaults to an empty list. (optional)
            vector_store_id: The vector store id. Defaults to None. (optional)
            metadata: The metadata. Defaults to an empty dictionary. (optional)

        Returns:
            str: The thread id.
        """
        create_thread_kwargs: dict[str, Any] = {}

        tool_resources = {}

        if code_interpreter_file_ids:
            tool_resources["code_interpreter"] = {"file_ids": code_interpreter_file_ids}

        if vector_store_id:
            tool_resources["file_search"] = {"vector_store_ids": [vector_store_id]}

        if tool_resources:
            create_thread_kwargs["tool_resources"] = tool_resources

        if messages:
            messages_to_add = []
            for message in messages:
                if message.role.value not in self.allowed_message_roles:
                    raise AgentExecutionException(
                        f"Invalid message role `{message.role.value}`. Allowed roles are {self.allowed_message_roles}."
                    )
                message_contents = get_message_contents(message=message)
                for content in message_contents:
                    messages_to_add.append({"role": message.role.value, "content": content})
            create_thread_kwargs["messages"] = messages_to_add

        if metadata:
            create_thread_kwargs["metadata"] = metadata

        thread = await self.client.beta.threads.create(**create_thread_kwargs)
        return thread.id

    async def delete_thread(self, thread_id: str) -> None:
        """Delete a thread.

        Args:
            thread_id: The thread id.
        """
        await self.client.beta.threads.delete(thread_id)

    async def delete(self) -> bool:
        """Delete the assistant.

        Returns:
            bool: True if the assistant is deleted.
        """
        if not self._is_deleted and self.assistant:
            await self.client.beta.assistants.delete(self.assistant.id)
            self._is_deleted = True
        return self._is_deleted

    async def add_chat_message(self, thread_id: str, message: "ChatMessageContent") -> "Message":
        """Add a chat message.

        Args:
            thread_id: The thread id.
            message: The chat message.

        Returns:
            Message: The message.
        """
        return await create_chat_message(self.client, thread_id, message, self.allowed_message_roles)

    async def get_thread_messages(self, thread_id: str) -> AsyncIterable["ChatMessageContent"]:
        """Get the messages for the specified thread.

        Args:
            thread_id: The thread id.

        Yields:
            ChatMessageContent: The chat message.
        """
        agent_names: dict[str, Any] = {}

        thread_messages = await self.client.beta.threads.messages.list(thread_id=thread_id, limit=100, order="desc")
        for message in thread_messages.data:
            assistant_name = None
            if message.assistant_id and message.assistant_id not in agent_names:
                agent = await self.client.beta.assistants.retrieve(message.assistant_id)
                if agent.name:
                    agent_names[message.assistant_id] = agent.name
            assistant_name = agent_names.get(message.assistant_id) if message.assistant_id else message.assistant_id
            assistant_name = assistant_name or message.assistant_id

            content: "ChatMessageContent" = generate_message_content(str(assistant_name), message)

            if len(content.items) > 0:
                yield content

    async def add_file(self, file_path: str, purpose: Literal["assistants", "vision"]) -> str:
        """Add a file for use with the Assistant.

        Args:
            file_path: The file path.
            purpose: The purpose. Can be "assistants" or "vision".

        Returns:
            str: The file id.

        Raises:
            AgentInitializationError: If the client has not been initialized or the file is not found.
        """
        try:
            with open(file_path, "rb") as file:
                file = await self.client.files.create(file=file, purpose=purpose)  # type: ignore
                return file.id  # type: ignore
        except FileNotFoundError as ex:
            raise AgentFileNotFoundException(f"File not found: {file_path}") from ex

    async def delete_file(self, file_id: str) -> None:
        """Delete a file.

        Args:
            file_id: The file id.
        """
        try:
            await self.client.files.delete(file_id)
        except Exception as ex:
            raise AgentExecutionException("Error deleting file.") from ex

    async def create_vector_store(self, file_ids: str | list[str]) -> str:
        """Create a vector store.

        Args:
            file_ids: The file ids either as a str of a single file ID or a list of strings of file IDs.

        Returns:
            The vector store id.

        Raises:
            AgentExecutionError: If there is an error creating the vector store.
        """
        if isinstance(file_ids, str):
            file_ids = [file_ids]
        try:
            vector_store = await self.client.beta.vector_stores.create(file_ids=file_ids)
            return vector_store.id
        except Exception as ex:
            raise AgentExecutionException("Error creating vector store.") from ex

    async def delete_vector_store(self, vector_store_id: str) -> None:
        """Delete a vector store.

        Args:
            vector_store_id: The vector store id.

        Raises:
            AgentExecutionError: If there is an error deleting the vector store.
        """
        try:
            await self.client.beta.vector_stores.delete(vector_store_id)
        except Exception as ex:
            raise AgentExecutionException("Error deleting vector store.") from ex

    # endregion

    # region Agent Invoke Methods

    @trace_agent_invocation
    async def invoke(
        self,
        thread_id: str,
        *,
        ai_model_id: str | None = None,
        enable_code_interpreter: bool | None = False,
        enable_file_search: bool | None = False,
        enable_json_response: bool | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the chat assistant.

        The supplied arguments will take precedence over the specified assistant level attributes.

        Args:
            thread_id: The thread id.
            ai_model_id: The AI model id. Defaults to None. (optional)
            enable_code_interpreter: Enable code interpreter. Defaults to False. (optional)
            enable_file_search: Enable file search. Defaults to False. (optional)
            enable_json_response: Enable JSON response. Defaults to False. (optional)
            max_completion_tokens: The max completion tokens. Defaults to None. (optional)
            max_prompt_tokens: The max prompt tokens. Defaults to None. (optional)
            parallel_tool_calls_enabled: Enable parallel tool calls. Defaults to True. (optional)
            truncation_message_count: The truncation message count. Defaults to None. (optional)
            temperature: The temperature. Defaults to None. (optional)
            top_p: The top p. Defaults to None. (optional)
            metadata: The metadata. Defaults to {}. (optional)
            kwargs: Extra keyword arguments.

        Yields:
            ChatMessageContent: The chat message content.
        """
        async for is_visible, content in self._invoke_internal(
            thread_id=thread_id,
            ai_model_id=ai_model_id,
            enable_code_interpreter=enable_code_interpreter,
            enable_file_search=enable_file_search,
            enable_json_response=enable_json_response,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            parallel_tool_calls_enabled=parallel_tool_calls_enabled,
            truncation_message_count=truncation_message_count,
            temperature=temperature,
            top_p=top_p,
            metadata=metadata,
            kwargs=kwargs,
        ):
            if is_visible:
                yield content

    async def _invoke_internal(
        self,
        thread_id: str,
        *,
        ai_model_id: str | None = None,
        enable_code_interpreter: bool | None = False,
        enable_file_search: bool | None = False,
        enable_json_response: bool | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Internal invoke method.

        The supplied arguments will take precedence over the specified assistant level attributes.

        Args:
            thread_id: The thread id.
            ai_model_id: The AI model id. Defaults to None. (optional)
            enable_code_interpreter: Enable code interpreter. Defaults to False. (optional)
            enable_file_search: Enable file search. Defaults to False. (optional)
            enable_json_response: Enable JSON response. Defaults to False. (optional)
            max_completion_tokens: The max completion tokens. Defaults to None. (optional)
            max_prompt_tokens: The max prompt tokens. Defaults to None. (optional)
            parallel_tool_calls_enabled: Enable parallel tool calls. Defaults to True. (optional)
            truncation_message_count: The truncation message count. Defaults to None. (optional)
            temperature: The temperature. Defaults to None. (optional)
            top_p: The top p. Defaults to None. (optional)
            metadata: The metadata. Defaults to {}. (optional)
            kwargs: Extra keyword arguments.

        Yields:
            tuple[bool, ChatMessageContent]: A tuple of visibility and chat message content.
        """
        if not self.assistant:
            raise AgentInitializationException("The assistant has not been created.")

        if self._is_deleted:
            raise AgentInitializationException("The assistant has been deleted.")

        if metadata is None:
            metadata = {}

        self._check_if_deleted()
        tools = self._get_tools()

        run_options = self._generate_options(
            ai_model_id=ai_model_id,
            enable_code_interpreter=enable_code_interpreter,
            enable_file_search=enable_file_search,
            enable_json_response=enable_json_response,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            parallel_tool_calls_enabled=parallel_tool_calls_enabled,
            truncation_message_count=truncation_message_count,
            temperature=temperature,
            top_p=top_p,
            metadata=metadata,
            kwargs=kwargs,
        )

        # Filter out None values to avoid passing them as kwargs
        run_options = {k: v for k, v in run_options.items() if v is not None}

        logger.debug(f"Starting invoke for agent `{self.name}` and thread `{thread_id}`")

        run = await self.client.beta.threads.runs.create(
            assistant_id=self.assistant.id,
            thread_id=thread_id,
            instructions=self.assistant.instructions,
            tools=tools,  # type: ignore
            **run_options,
        )

        processed_step_ids = set()
        function_steps: dict[str, "FunctionCallContent"] = {}

        while run.status != "completed":
            run = await self._poll_run_status(run=run, thread_id=thread_id)

            if run.status in self.error_message_states:
                error_message = ""
                if run.last_error and run.last_error.message:
                    error_message = run.last_error.message
                raise AgentInvokeException(
                    f"Run failed with status: `{run.status}` for agent `{self.name}` and thread `{thread_id}` "
                    f"with error: {error_message}"
                )

            # Check if function calling required
            if run.status == "requires_action":
                logger.debug(f"Run [{run.id}] requires action for agent `{self.name}` and thread `{thread_id}`")
                fccs = get_function_call_contents(run, function_steps)
                if fccs:
                    logger.debug(
                        f"Yielding `generate_function_call_content` for agent `{self.name}` and "
                        f"thread `{thread_id}`, visibility False"
                    )
                    yield False, generate_function_call_content(agent_name=self.name, fccs=fccs)

                    from semantic_kernel.contents.chat_history import ChatHistory

                    chat_history = ChatHistory()
                    _ = await self._invoke_function_calls(fccs=fccs, chat_history=chat_history)

                    tool_outputs = self._format_tool_outputs(fccs, chat_history)
                    await self.client.beta.threads.runs.submit_tool_outputs(
                        run_id=run.id,
                        thread_id=thread_id,
                        tool_outputs=tool_outputs,  # type: ignore
                    )
                    logger.debug(f"Submitted tool outputs for agent `{self.name}` and thread `{thread_id}`")

            steps_response = await self.client.beta.threads.runs.steps.list(run_id=run.id, thread_id=thread_id)
            logger.debug(f"Called for steps_response for run [{run.id}] agent `{self.name}` and thread `{thread_id}`")
            steps: list[RunStep] = steps_response.data

            def sort_key(step: RunStep):
                # Put tool_calls first, then message_creation
                # If multiple steps share a type, break ties by completed_at
                return (0 if step.type == "tool_calls" else 1, step.completed_at)

            completed_steps_to_process = sorted(
                [s for s in steps if s.completed_at is not None and s.id not in processed_step_ids], key=sort_key
            )

            logger.debug(
                f"Completed steps to process for run [{run.id}] agent `{self.name}` and thread `{thread_id}` "
                f"with length `{len(completed_steps_to_process)}`"
            )

            message_count = 0
            for completed_step in completed_steps_to_process:
                if completed_step.type == "tool_calls":
                    logger.debug(
                        f"Entering step type tool_calls for run [{run.id}], agent `{self.name}` and "
                        f"thread `{thread_id}`"
                    )
                    assert hasattr(completed_step.step_details, "tool_calls")  # nosec
                    for tool_call in completed_step.step_details.tool_calls:
                        is_visible = False
                        content: "ChatMessageContent | None" = None
                        if tool_call.type == "code_interpreter":
                            logger.debug(
                                f"Entering step type tool_calls for run [{run.id}], [code_interpreter] for "
                                f"agent `{self.name}` and thread `{thread_id}`"
                            )
                            content = generate_code_interpreter_content(
                                self.name,
                                tool_call.code_interpreter.input,  # type: ignore
                            )
                            is_visible = True
                        elif tool_call.type == "function":
                            logger.debug(
                                f"Entering step type tool_calls for run [{run.id}], [function] for agent `{self.name}` "
                                f"and thread `{thread_id}`"
                            )
                            function_step = function_steps.get(tool_call.id)
                            assert function_step is not None  # nosec
                            content = generate_function_result_content(
                                agent_name=self.name, function_step=function_step, tool_call=tool_call
                            )

                        if content:
                            message_count += 1
                            logger.debug(
                                f"Yielding tool_message for run [{run.id}], agent `{self.name}` and thread "
                                f"`{thread_id}` and message count `{message_count}`, is_visible `{is_visible}`"
                            )
                            yield is_visible, content
                elif completed_step.type == "message_creation":
                    logger.debug(
                        f"Entering step type message_creation for run [{run.id}], agent `{self.name}` and "
                        f"thread `{thread_id}`"
                    )
                    message = await self._retrieve_message(
                        thread_id=thread_id,
                        message_id=completed_step.step_details.message_creation.message_id,  # type: ignore
                    )
                    if message:
                        content = generate_message_content(self.name, message)
                        if content and len(content.items) > 0:
                            message_count += 1
                            logger.debug(
                                f"Yielding message_creation for run [{run.id}], agent `{self.name}` and "
                                f"thread `{thread_id}` and message count `{message_count}`, is_visible `{True}`"
                            )
                            yield True, content
                processed_step_ids.add(completed_step.id)

    @trace_agent_invocation
    async def invoke_stream(
        self,
        thread_id: str,
        *,
        messages: list["ChatMessageContent"] | None = None,
        ai_model_id: str | None = None,
        enable_code_interpreter: bool | None = False,
        enable_file_search: bool | None = False,
        enable_json_response: bool | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the chat assistant with streaming."""
        async for content in self._invoke_internal_stream(
            thread_id=thread_id,
            messages=messages,
            ai_model_id=ai_model_id,
            enable_code_interpreter=enable_code_interpreter,
            enable_file_search=enable_file_search,
            enable_json_response=enable_json_response,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            parallel_tool_calls_enabled=parallel_tool_calls_enabled,
            truncation_message_count=truncation_message_count,
            temperature=temperature,
            top_p=top_p,
            metadata=metadata,
            **kwargs,
        ):
            yield content

    async def _invoke_internal_stream(
        self,
        thread_id: str,
        *,
        messages: list["ChatMessageContent"] | None = None,
        ai_model_id: str | None = None,
        enable_code_interpreter: bool | None = False,
        enable_file_search: bool | None = False,
        enable_json_response: bool | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Internal invoke method with streaming."""
        if not self.assistant:
            raise AgentInitializationException("The assistant has not been created.")

        if self._is_deleted:
            raise AgentInitializationException("The assistant has been deleted.")

        if metadata is None:
            metadata = {}

        tools = self._get_tools()

        run_options = self._generate_options(
            ai_model_id=ai_model_id,
            enable_code_interpreter=enable_code_interpreter,
            enable_file_search=enable_file_search,
            enable_json_response=enable_json_response,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            parallel_tool_calls_enabled=parallel_tool_calls_enabled,
            truncation_message_count=truncation_message_count,
            temperature=temperature,
            top_p=top_p,
            metadata=metadata,
            **kwargs,
        )

        # Filter out None values to avoid passing them as kwargs
        run_options = {k: v for k, v in run_options.items() if v is not None}

        stream = self.client.beta.threads.runs.stream(
            assistant_id=self.assistant.id,
            thread_id=thread_id,
            instructions=self.assistant.instructions,
            tools=tools,  # type: ignore
            **run_options,
        )

        function_steps: dict[str, "FunctionCallContent"] = {}
        active_messages: dict[str, RunStep] = {}

        while True:
            async with stream as response_stream:
                async for event in response_stream:
                    if event.event == "thread.run.created":
                        run = event.data
                        logger.info(f"Assistant run created with ID: {run.id}")
                    elif event.event == "thread.run.in_progress":
                        run = event.data
                        logger.info(f"Assistant run in progress with ID: {run.id}")
                    elif event.event == "thread.message.delta":
                        content = generate_streaming_message_content(self.name, event.data)
                        yield content
                    elif event.event == "thread.run.step.completed":
                        logger.info(f"Run step completed with ID: {event.data.id}")
                        if hasattr(event.data.step_details, "message_creation"):
                            message_id = event.data.step_details.message_creation.message_id
                            if message_id not in active_messages:
                                active_messages[message_id] = event.data
                    elif event.event == "thread.run.step.delta":
                        step_details = event.data.delta.step_details
                        if (
                            step_details is not None
                            and hasattr(step_details, "tool_calls")
                            and step_details.tool_calls is not None
                            and isinstance(step_details.tool_calls, list)
                        ):
                            for tool_call in step_details.tool_calls:
                                tool_content = None
                                if tool_call.type == "function":
                                    tool_content = generate_streaming_function_content(self.name, step_details)
                                elif tool_call.type == "code_interpreter":
                                    tool_content = generate_streaming_code_interpreter_content(self.name, step_details)
                                if tool_content:
                                    yield tool_content
                    elif event.event == "thread.run.requires_action":
                        run = event.data
                        function_action_result = await self._handle_streaming_requires_action(run, function_steps)
                        if function_action_result is None:
                            raise AgentInvokeException(
                                f"Function call required but no function steps found for agent `{self.name}` "
                                f"thread: {thread_id}."
                            )
                        if function_action_result.function_result_content:
                            # Yield the function result content to the caller
                            yield function_action_result.function_result_content
                            if messages is not None:
                                # Add the function result content to the messages list, if it exists
                                messages.append(function_action_result.function_result_content)
                        if function_action_result.function_call_content:
                            if messages is not None:
                                messages.append(function_action_result.function_call_content)
                            stream = self.client.beta.threads.runs.submit_tool_outputs_stream(
                                run_id=run.id,
                                thread_id=thread_id,
                                tool_outputs=function_action_result.tool_outputs,  # type: ignore
                            )
                            break
                    elif event.event == "thread.run.completed":
                        run = event.data
                        logger.info(f"Run completed with ID: {run.id}")
                        if len(active_messages) > 0:
                            for id in active_messages:
                                step: RunStep = active_messages[id]
                                message = await self._retrieve_message(
                                    thread_id=thread_id,
                                    message_id=id,  # type: ignore
                                )

                                if message and message.content:
                                    content = generate_message_content(self.name, message, step)
                                    if messages is not None:
                                        messages.append(content)
                        return
                    elif event.event == "thread.run.failed":
                        run = event.data  # type: ignore
                        error_message = ""
                        if run.last_error and run.last_error.message:
                            error_message = run.last_error.message
                        raise AgentInvokeException(
                            f"Run failed with status: `{run.status}` for agent `{self.name}` and thread `{thread_id}` "
                            f"with error: {error_message}"
                        )
                else:
                    # If the inner loop completes without encountering a 'break', exit the outer loop
                    break

    async def _handle_streaming_requires_action(
        self, run: Run, function_steps: dict[str, "FunctionCallContent"]
    ) -> FunctionActionResult | None:
        fccs = get_function_call_contents(run, function_steps)
        if fccs:
            function_call_content = generate_function_call_content(agent_name=self.name, fccs=fccs)

            from semantic_kernel.contents.chat_history import ChatHistory

            chat_history = ChatHistory()
            _ = await self._invoke_function_calls(fccs=fccs, chat_history=chat_history)

            function_result_content = merge_function_results(chat_history.messages)[0]

            tool_outputs = self._format_tool_outputs(fccs, chat_history)
            return FunctionActionResult(function_call_content, function_result_content, tool_outputs)
        return None

    # endregion

    # region Agent Helper Methods

    def _generate_options(
        self,
        *,
        ai_model_id: str | None = None,
        enable_code_interpreter: bool | None = False,
        enable_file_search: bool | None = False,
        enable_json_response: bool | None = False,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        metadata: dict[str, str] | None = {},
        kwargs: Any = {},
    ) -> dict[str, Any]:
        """Generate options for the assistant invocation."""
        merged_options = self._merge_options(
            ai_model_id=ai_model_id,
            enable_code_interpreter=enable_code_interpreter,
            enable_file_search=enable_file_search,
            enable_json_response=enable_json_response,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            parallel_tool_calls_enabled=parallel_tool_calls_enabled,
            truncation_message_count=truncation_message_count,
            temperature=temperature,
            top_p=top_p,
            metadata=metadata,
            **kwargs,
        )

        truncation_message_count = merged_options.get("truncation_message_count")

        return {
            "max_completion_tokens": merged_options.get("max_completion_tokens"),
            "max_prompt_tokens": merged_options.get("max_prompt_tokens"),
            "model": merged_options.get("ai_model_id"),
            "top_p": merged_options.get("top_p"),
            # TODO(evmattso): Support `parallel_tool_calls` when it is ready
            "response_format": "json" if merged_options.get("enable_json_response") else None,
            "temperature": merged_options.get("temperature"),
            "truncation_strategy": truncation_message_count if truncation_message_count else None,
            "metadata": merged_options.get("metadata", None),
        }

    def _merge_options(
        self,
        ai_model_id: str | None = None,
        enable_code_interpreter: bool | None = None,
        enable_file_search: bool | None = None,
        enable_json_response: bool | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        metadata: dict[str, str] | None = {},
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Merge the run-time options with the agent level attribute options."""
        merged_options = {
            "ai_model_id": ai_model_id if ai_model_id is not None else self.ai_model_id,
            "enable_code_interpreter": enable_code_interpreter
            if enable_code_interpreter is not None
            else self.enable_code_interpreter,
            "enable_file_search": enable_file_search if enable_file_search is not None else self.enable_file_search,
            "enable_json_response": enable_json_response
            if enable_json_response is not None
            else self.enable_json_response,
            "max_completion_tokens": max_completion_tokens
            if max_completion_tokens is not None
            else self.max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens if max_prompt_tokens is not None else self.max_prompt_tokens,
            "parallel_tool_calls_enabled": parallel_tool_calls_enabled
            if parallel_tool_calls_enabled is not None
            else self.parallel_tool_calls_enabled,
            "truncation_message_count": truncation_message_count
            if truncation_message_count is not None
            else self.truncation_message_count,
            "temperature": temperature if temperature is not None else self.temperature,
            "top_p": top_p if top_p is not None else self.top_p,
            "metadata": metadata if metadata is not None else self.metadata,
        }

        # Update merged_options with any additional kwargs
        merged_options.update(kwargs)
        return merged_options

    async def _poll_run_status(self, run: Run, thread_id: str) -> Run:
        """Poll the run status.

        Args:
            run: The run.
            thread_id: The thread id.

        Returns:
            The updated run.
        """
        logger.info(f"Polling run status: {run.id}, threadId: {thread_id}")

        count = 0

        try:
            run = await asyncio.wait_for(
                self._poll_loop(run, thread_id, count), timeout=self.polling_options.run_polling_timeout.total_seconds()
            )
        except asyncio.TimeoutError:
            timeout_duration = self.polling_options.run_polling_timeout
            error_message = f"Polling timed out for run id: `{run.id}` and thread id: `{thread_id}` after waiting {timeout_duration}."  # noqa: E501
            logger.error(error_message)
            raise AgentInvokeException(error_message)

        logger.info(f"Polled run status: {run.status}, {run.id}, threadId: {thread_id}")
        return run

    async def _poll_loop(self, run: Run, thread_id: str, count: int) -> Run:
        """Internal polling loop."""
        while True:
            await asyncio.sleep(self.polling_options.get_polling_interval(count).total_seconds())
            count += 1

            try:
                run = await self.client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)
            except Exception as e:
                logging.warning(f"Failed to retrieve run for run id: `{run.id}` and thread id: `{thread_id}`: {e}")
                # Retry anyway

            if run.status not in self.polling_status:
                break

        return run

    async def _retrieve_message(self, thread_id: str, message_id: str) -> Message | None:
        """Retrieve a message from a thread.

        Args:
            thread_id: The thread id.
            message_id: The message id.

        Returns:
            The message or None.
        """
        message: Message | None = None
        count = 0
        max_retries = 3

        while count < max_retries:
            try:
                message = await self.client.beta.threads.messages.retrieve(message_id, thread_id=thread_id)
                break
            except Exception as ex:
                logger.error(f"Failed to retrieve message {message_id} from thread {thread_id}: {ex}")
                count += 1
                if count >= max_retries:
                    logger.error(
                        f"Max retries reached. Unable to retrieve message {message_id} from thread {thread_id}."
                    )
                    break
                backoff_time: float = self.polling_options.message_synchronization_delay.total_seconds() * (2**count)
                await asyncio.sleep(backoff_time)

        return message

    def _check_if_deleted(self) -> None:
        """Check if the assistant has been deleted."""
        if self._is_deleted:
            raise AgentInitializationException("The assistant has been deleted.")

    def _get_tools(self) -> list[dict[str, str]]:
        """Get the list of tools for the assistant.

        Returns:
            The list of tools.
        """
        tools = []
        if self.assistant is None:
            raise AgentInitializationException("The assistant has not been created.")

        for tool in self.assistant.tools:
            if isinstance(tool, CodeInterpreterTool):
                tools.append({"type": "code_interpreter"})
            elif isinstance(tool, FileSearchTool):
                tools.append({"type": "file_search"})

        funcs = self.kernel.get_full_list_of_function_metadata()
        tools.extend([kernel_function_metadata_to_function_call_format(f) for f in funcs])

        return tools

    async def _invoke_function_calls(self, fccs: list["FunctionCallContent"], chat_history: "ChatHistory") -> list[Any]:
        """Invoke function calls and store results in chat history.

        Args:
            fccs: The function call contents.
            chat_history: The chat history.

        Returns:
            The results as a list.
        """
        tasks = [
            self.kernel.invoke_function_call(function_call=function_call, chat_history=chat_history)
            for function_call in fccs
        ]
        return await asyncio.gather(*tasks)

    def _format_tool_outputs(
        self, fccs: list["FunctionCallContent"], chat_history: "ChatHistory"
    ) -> list[dict[str, str]]:
        """Format tool outputs from chat history for submission.

        Args:
            fccs: The function call contents.
            chat_history: The chat history.

        Returns:
            The formatted tool outputs as a list of dictionaries.
        """
        from semantic_kernel.contents.function_result_content import FunctionResultContent

        tool_call_lookup = {
            tool_call.id: tool_call
            for message in chat_history.messages
            for tool_call in message.items
            if isinstance(tool_call, FunctionResultContent)
        }

        return [
            {"tool_call_id": fcc.id, "output": str(tool_call_lookup[fcc.id].result)}
            for fcc in fccs
            if fcc.id in tool_call_lookup
        ]

    # endregion
