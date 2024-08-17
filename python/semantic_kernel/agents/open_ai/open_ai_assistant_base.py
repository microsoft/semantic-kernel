# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from openai import AsyncOpenAI
from openai.resources.beta.assistants import Assistant
from openai.resources.beta.threads.messages import Message
from openai.resources.beta.threads.runs.runs import Run
from openai.types.beta import AssistantResponseFormat
from openai.types.beta.assistant_tool import CodeInterpreterTool, FileSearchTool
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.runs import RunStep
from openai.types.beta.threads.text_content_block import TextContentBlock
from pydantic import Field

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import (
    AgentExecutionError,
    AgentFileNotFoundException,
    AgentInitializationError,
    AgentInvokeError,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from openai.types.beta.threads.annotation import Annotation
    from openai.types.beta.threads.runs.tool_call import ToolCall
    from openai.types.file_object import FileObject

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
    enable_code_interpreter: bool | None = Field(False)
    enable_file_search: bool | None = Field(False)
    enable_json_response: bool | None = Field(False)
    file_ids: list[str] | None = Field(default_factory=list, max_length=20)
    temperature: float | None = Field(None)
    top_p: float | None = Field(None)
    vector_store_id: str | None = None
    metadata: dict[str, Any] | None = Field(default_factory=dict, max_length=16)
    max_completion_tokens: int | None = Field(None)
    max_prompt_tokens: int | None = Field(None)
    parallel_tool_calls_enabled: bool | None = Field(True)
    truncation_message_count: int | None = Field(None)

    allowed_message_roles: ClassVar[list[str]] = [AuthorRole.USER, AuthorRole.ASSISTANT]
    polling_status: ClassVar[list[str]] = ["queued", "in_progress", "cancelling"]
    error_message_states: ClassVar[list[str]] = ["failed", "canceled", "expired"]

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
        file_ids: list[str] | None = [],
        temperature: float | None = None,
        top_p: float | None = None,
        vector_store_id: str | None = None,
        metadata: dict[str, Any] | None = {},
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAIAssistant Base.

        Args:
            ai_model_id (str): The AI model id. Defaults to None.
            client (AsyncOpenAI): The client, either AsyncOpenAI or AsyncAzureOpenAI.
            service_id (str): The service id.
            kernel (Kernel): The kernel. (optional)
            id (str): The id. Defaults to None. (optional)
            name (str): The name. Defaults to None. (optional)
            description (str): The description. Defaults to None. (optional)
            default_headers (dict[str, str]): The default headers. Defaults to None. (optional)
            instructions (str): The instructions. Defaults to None. (optional)
            enable_code_interpreter (bool): Enable code interpreter. Defaults to False. (optional)
            enable_file_search (bool): Enable file search. Defaults to False. (optional)
            enable_json_response (bool): Enable JSON response. Defaults to False. (optional)
            file_ids (list[str]): The file ids. Defaults to []. (optional)
            temperature (float): The temperature. Defaults to None. (optional)
            top_p (float): The top p. Defaults to None. (optional)
            vector_store_id (str): The vector store id. Defaults to None. (optional)
            metadata (dict[str, Any]): The metadata. Defaults to {}. (optional)
            max_completion_tokens (int): The max completion tokens. Defaults to None. (optional)
            max_prompt_tokens (int): The max prompt tokens. Defaults to None. (optional)
            parallel_tool_calls_enabled (bool): Enable parallel tool calls. Defaults to True. (optional)
            truncation_message_count (int): The truncation message count. Defaults to None. (optional)
            kwargs (Any): The keyword arguments.
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
            "file_ids": file_ids,
            "temperature": temperature,
            "top_p": top_p,
            "vector_store_id": vector_store_id,
            "metadata": metadata,
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
        enable_file_search: bool | None = None,
        file_ids: list[str] | None = None,
        vector_store_id: str | None = None,
        metadata: dict[str, str] | None = {},
        **kwargs: Any,
    ) -> "Assistant":
        """Create the assistant.

        Args:
            ai_model_id (str): The AI model id. Defaults to None. (optional)
            description (str): The description. Defaults to None. (optional)
            instructions (str): The instructions. Defaults to None. (optional)
            name (str): The name. Defaults to None. (optional)
            enable_code_interpreter (bool): Enable code interpreter. Defaults to None. (optional)
            enable_file_search (bool): Enable file search. Defaults to None. (optional)
            file_ids (list[str]): The file ids. Defaults to None. (optional)
            vector_store_id (str): The vector store id. Defaults to None. (optional)
            metadata (dict[str, str]): The metadata. Defaults to {}. (optional)
            kwargs (Any): Extra keyword arguments.

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
        if file_ids is not None:
            tool_resources["code_interpreter"] = {"file_ids": file_ids}
        elif self.file_ids:
            tool_resources["code_interpreter"] = {"file_ids": self.file_ids}

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

        execution_settings = {}
        if self.max_completion_tokens:
            execution_settings["max_completion_tokens"] = self.max_completion_tokens

        if self.max_prompt_tokens:
            execution_settings["max_prompt_tokens"] = self.max_prompt_tokens

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
                file_ids = getattr(tool_resources.code_interpreter, "file_ids", [])

            if hasattr(tool_resources, "file_search") and tool_resources.file_search:
                vector_store_ids = getattr(tool_resources.file_search, "vector_store_ids", [])
                if vector_store_ids:
                    vector_store_id = vector_store_ids[0]

        enable_json_response = (
            hasattr(assistant, "response_format")
            and isinstance(assistant.response_format, AssistantResponseFormat)
            and assistant.response_format.type == "json_object"
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
            "file_ids": file_ids,
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
            raise AgentInitializationError("The assistant has not been created.")
        return self._get_tools()

    # endregion

    # region Agent Methods

    async def create_thread(
        self,
        *,
        code_interpreter_file_ids: list[str] | None = [],
        messages: list[ChatMessageContent] | None = [],
        vector_store_id: str | None = None,
        metadata: dict[str, str] = {},
    ) -> str:
        """Create a thread.

        Args:
            code_interpreter_file_ids (list[str]): The code interpreter file ids. Defaults to []. (optional)
            messages (list[ChatMessageContent]): The chat messages. Defaults to []. (optional)
            vector_store_id (str): The vector store id. Defaults to None. (optional)
            metadata (dict[str, str]): The metadata. Defaults to {}. (optional)

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
                    raise AgentExecutionError(
                        f"Invalid message role `{message.role.value}`. Allowed roles are {self.allowed_message_roles}."
                    )
                message_contents = self._get_message_contents(message=message)
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
            thread_id (str): The thread id.
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

    async def add_file(self, file_path: str, purpose: Literal["assistants", "vision"]) -> str:
        """Add a file.

        Args:
            file_path (str): The file path.
            purpose (str): The purpose. Can be "assistants" or "vision".

        Returns:
            str: The file id.

        Raises:
            AgentInitializationError: If the client has not been initialized or the file is not found.
        """
        try:
            with open(file_path, "rb") as file:
                file: "FileObject" = await self.client.files.create(file=file, purpose=purpose)  # type: ignore
                return file.id  # type: ignore
        except FileNotFoundError as ex:
            raise AgentFileNotFoundException(f"File not found: {file_path}") from ex

    async def add_chat_message(self, thread_id: str, message: ChatMessageContent) -> "Message":
        """Add a chat message.

        Args:
            thread_id (str): The thread id.
            message (ChatMessageContent): The chat message.

        Returns:
            Message: The message.
        """
        if message.role.value not in self.allowed_message_roles:
            raise AgentExecutionError(
                f"Invalid message role `{message.role.value}`. Allowed roles are {self.allowed_message_roles}."
            )

        metadata: Any = None
        if message.metadata:
            metadata = message.metadata

        message_contents: list[dict[str, Any]] = self._get_message_contents(message=message)

        return await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role=message.role.value,  # type: ignore
            content=message_contents,  # type: ignore
            metadata=metadata,
        )

    async def get_thread_messages(self, thread_id: str) -> AsyncIterable[ChatMessageContent]:
        """Get the messages for the specified thread.

        Args:
            thread_id (str): The thread id.

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

            content: ChatMessageContent = self._generate_message_content(str(assistant_name), message)

            if len(content.items) > 0:
                yield content

    # region Agent Invoke Methods

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
        metadata: dict[str, str] | None = {},
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke the chat assistant.

        The supplied arguments will take precedence over the specified assistant level attributes.

        Args:
            thread_id (str): The thread id.
            ai_model_id (str): The AI model id. Defaults to None. (optional)
            enable_code_interpreter (bool): Enable code interpreter. Defaults to False. (optional)
            enable_file_search (bool): Enable file search. Defaults to False. (optional)
            enable_json_response (bool): Enable JSON response. Defaults to False. (optional)
            max_completion_tokens (int): The max completion tokens. Defaults to None. (optional)
            max_prompt_tokens (int): The max prompt tokens. Defaults to None. (optional)
            parallel_tool_calls_enabled (bool): Enable parallel tool calls. Defaults to True. (optional)
            truncation_message_count (int): The truncation message count. Defaults to None. (optional)
            temperature (float): The temperature. Defaults to None. (optional)
            top_p (float): The top p. Defaults to None. (optional)
            metadata (dict[str, str]): The metadata. Defaults to {}. (optional)
            kwargs (Any): Extra keyword arguments.

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
        metadata: dict[str, str] | None = {},
        kwargs: Any,
    ) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
        """Internal invoke method.

        The supplied arguments will take precedence over the specified assistant level attributes.

        Args:
            thread_id (str): The thread id.
            ai_model_id (str): The AI model id. Defaults to None. (optional)
            enable_code_interpreter (bool): Enable code interpreter. Defaults to False. (optional)
            enable_file_search (bool): Enable file search. Defaults to False. (optional)
            enable_json_response (bool): Enable JSON response. Defaults to False. (optional)
            max_completion_tokens (int): The max completion tokens. Defaults to None. (optional)
            max_prompt_tokens (int): The max prompt tokens. Defaults to None. (optional)
            parallel_tool_calls_enabled (bool): Enable parallel tool calls. Defaults to True. (optional)
            truncation_message_count (int): The truncation message count. Defaults to None. (optional)
            temperature (float): The temperature. Defaults to None. (optional)
            top_p (float): The top p. Defaults to None. (optional)
            metadata (dict[str, str]): The metadata. Defaults to {}. (optional)
            kwargs (Any): Extra keyword arguments.

        Yields:
            tuple[bool, ChatMessageContent]: A tuple of visibility and chat message content.
        """
        if not self.assistant:
            raise AgentInitializationError("The assistant has not been created.")

        if self._is_deleted:
            raise AgentInitializationError("The assistant has been deleted.")

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

        run = await self.client.beta.threads.runs.create(
            assistant_id=self.assistant.id,
            thread_id=thread_id,
            instructions=self.assistant.instructions,
            tools=tools,  # type: ignore
            **run_options,
        )

        processed_step_ids = set()
        function_steps: dict[str, FunctionCallContent] = {}

        while run.status != "completed":
            run = await self._poll_run_status(run=run, thread_id=thread_id)

            if run.status in self.error_message_states:
                raise AgentInvokeError(
                    f"Run failed with status: `{run.status}` for agent `{self.name}` and thread `{thread_id}`"
                )

            # Check if function calling required
            if run.status == "requires_action":
                fccs = self._get_function_call_contents(run, function_steps)
                if fccs:
                    yield False, self._generate_function_call_content(agent_name=self.name, fccs=fccs)

                    chat_history = ChatHistory()
                    _ = await self._invoke_function_calls(fccs=fccs, chat_history=chat_history)

                    tool_outputs = self._format_tool_outputs(chat_history)
                    await self.client.beta.threads.runs.submit_tool_outputs(
                        run_id=run.id,
                        thread_id=thread_id,
                        tool_outputs=tool_outputs,  # type: ignore
                    )

            steps_response = await self.client.beta.threads.runs.steps.list(run_id=run.id, thread_id=thread_id)
            steps: list[RunStep] = steps_response.data
            completed_steps_to_process: list[RunStep] = sorted(
                [s for s in steps if s.completed_at is not None and s.id not in processed_step_ids],
                key=lambda s: s.created_at,
            )

            message_count = 0
            for completed_step in completed_steps_to_process:
                if completed_step.type == "tool_calls":
                    assert hasattr(completed_step.step_details, "tool_calls")  # nosec
                    for tool_call in completed_step.step_details.tool_calls:
                        is_visible = False
                        content: ChatMessageContent | None = None
                        if tool_call.type == "code_interpreter":
                            content = self._generate_code_interpreter_content(
                                self.name,
                                tool_call.code_interpreter.input,  # type: ignore
                            )
                            is_visible = True
                        elif tool_call.type == "function":
                            function_step = function_steps.get(tool_call.id)
                            assert function_step is not None  # nosec
                            content = self._generate_function_result_content(
                                agent_name=self.name, function_step=function_step, tool_call=tool_call
                            )

                        if content:
                            message_count += 1
                            yield is_visible, content
                elif completed_step.type == "message_creation":
                    message = await self._retrieve_message(
                        thread_id=thread_id,
                        message_id=completed_step.step_details.message_creation.message_id,  # type: ignore
                    )
                    if message:
                        content = self._generate_message_content(self.name, message)
                        if len(content.items) > 0:
                            message_count += 1
                            yield True, content
                processed_step_ids.add(completed_step.id)

    # endregion

    # region Content Generation Methods

    def _generate_function_call_content(self, agent_name: str, fccs: list[FunctionCallContent]) -> ChatMessageContent:
        """Generate function call content."""
        function_call_content: ChatMessageContent = ChatMessageContent(role=AuthorRole.TOOL, name=agent_name)  # type: ignore

        function_call_content.items.extend(fccs)

        return function_call_content

    def _generate_function_result_content(
        self, agent_name: str, function_step: FunctionCallContent, tool_call: "ToolCall"
    ) -> ChatMessageContent:
        """Generate function result content."""
        function_call_content: ChatMessageContent = ChatMessageContent(role=AuthorRole.TOOL, name=agent_name)  # type: ignore
        function_call_content.items.append(
            FunctionResultContent(
                function_name=function_step.function_name,
                plugin_name=function_step.plugin_name,
                id=function_step.id,
                result=tool_call.function.output,  # type: ignore
            )
        )
        return function_call_content

    def _generate_code_interpreter_content(self, agent_name: str, code: str) -> ChatMessageContent:
        """Generate code interpreter content."""
        return ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            content=code,
            name=agent_name,
            metadata={"code": True},
        )

    def _generate_annotation_content(self, annotation: "Annotation") -> AnnotationContent:
        """Generate annotation content."""
        file_id = None
        if hasattr(annotation, "file_path"):
            file_id = annotation.file_path.file_id
        elif hasattr(annotation, "file_citation"):
            file_id = annotation.file_citation.file_id

        return AnnotationContent(
            file_id=file_id,
            quote=annotation.text,
            start_index=annotation.start_index,
            end_index=annotation.end_index,
        )

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
        """Poll the run status."""
        logger.info(f"Polling run status: {run.id}, threadId: {thread_id}")

        count = 0

        while True:
            # Reduce polling frequency after a couple attempts
            await asyncio.sleep(self.polling_options.get_polling_interval(count).total_seconds())
            count += 1

            try:
                run = await self.client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)
            except Exception as e:
                logging.warning(f"Failed to retrieve run for run id: `{run.id}` and thread id: `{thread_id}`: {e}")
                # Retry anyway

            if run.status not in self.polling_status:
                break

        logger.info(f"Polled run status: {run.status}, {run.id}, threadId: {thread_id}")
        return run

    async def _retrieve_message(self, thread_id: str, message_id: str) -> Message | None:
        """Retrieve a message from a thread."""
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

    def _get_message_contents(self, message: ChatMessageContent) -> list[dict[str, Any]]:
        """Get the message contents."""
        contents: list[dict[str, Any]] = []
        for content in message.items:
            if isinstance(content, TextContent):
                contents.append({"type": "text", "text": content.text})
            elif isinstance(content, ImageContent) and content.uri:
                contents.append(content.to_dict())
        return contents

    def _generate_message_content(self, assistant_name: str, message: Message) -> ChatMessageContent:
        """Generate message content."""
        role = AuthorRole(message.role)

        content: ChatMessageContent = ChatMessageContent(role=role, name=assistant_name)  # type: ignore

        for item_content in message.content:
            if item_content.type == "text":
                assert isinstance(item_content, TextContentBlock)  # nosec
                content.items.append(
                    TextContent(
                        text=item_content.text.value,
                    )
                )
                for annotation in item_content.text.annotations:
                    content.items.append(self._generate_annotation_content(annotation))
            elif item_content.type == "image_file":
                assert isinstance(item_content, ImageFileContentBlock)  # nosec
                content.items.append(
                    FileReferenceContent(
                        file_id=item_content.image_file.file_id,
                    )
                )
        return content

    def _check_if_deleted(self) -> None:
        """Check if the assistant has been deleted."""
        if self._is_deleted:
            raise AgentInitializationError("The assistant has been deleted.")

    def _get_tools(self) -> list[dict[str, str]]:
        """Get the list of tools for the assistant.

        Returns:
            list[dict[str, str]]: The list of tools.
        """
        tools = []
        if self.assistant is None:
            raise AgentInitializationError("The assistant has not been created.")

        for tool in self.assistant.tools:
            if isinstance(tool, CodeInterpreterTool):
                tools.append({"type": "code_interpreter"})
            elif isinstance(tool, FileSearchTool):
                tools.append({"type": "file_search"})

        funcs = self.kernel.get_full_list_of_function_metadata()
        tools.extend([kernel_function_metadata_to_function_call_format(f) for f in funcs])

        return tools

    def _get_function_call_contents(
        self, run: Run, function_steps: dict[str, FunctionCallContent]
    ) -> list[FunctionCallContent]:
        """Extract function call contents from the run.

        Args:
            run (Run): The run.
            function_steps (dict[str, FunctionCallContent]): The function steps

        Returns:
            list[FunctionCallContent]: The list of function call contents.
        """
        function_call_contents: list[FunctionCallContent] = []
        required_action = getattr(run, "required_action", None)
        if not required_action or not getattr(required_action, "submit_tool_outputs", False):
            return function_call_contents
        for tool in required_action.submit_tool_outputs.tool_calls:
            fcc = FunctionCallContent(
                id=tool.id,
                index=getattr(tool, "index", None),
                name=tool.function.name,
                arguments=tool.function.arguments,
            )
            function_call_contents.append(fcc)
            function_steps[tool.id] = fcc
        return function_call_contents

    async def _invoke_function_calls(self, fccs: list[FunctionCallContent], chat_history: ChatHistory) -> list[Any]:
        """Invoke function calls and store results in chat history.

        Args:
            fccs (List[FunctionCallContent]): The function call contents.
            chat_history (ChatHistory): The chat history.

        Returns:
            List[Any]: The results.
        """
        tasks = [
            self.kernel.invoke_function_call(function_call=function_call, chat_history=chat_history)
            for function_call in fccs
        ]
        return await asyncio.gather(*tasks)

    def _format_tool_outputs(self, chat_history: ChatHistory) -> list[dict[str, str]]:
        """Format tool outputs from chat history for submission.

        Args:
            chat_history (ChatHistory): The chat history.

        Returns:
            list[dict[str, str]]: The formatted tool outputs
        """
        tool_outputs = []
        for tool_call in chat_history.messages[0].items:
            if isinstance(tool_call, FunctionResultContent):
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": tool_call.result,
                    }
                )
        return tool_outputs

    # endregion
