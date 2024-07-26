# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from openai import AsyncOpenAI
from openai.resources.beta.assistants import Assistant
from openai.resources.beta.threads.messages import Message
from openai.resources.beta.threads.runs.runs import Run
from openai.types.beta.threads.runs import RunStep
from pydantic import Field

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.open_ai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.agents.open_ai.open_ai_service_configuration import OpenAIServiceConfiguration
from semantic_kernel.agents.open_ai.open_ai_thread_creation_options import OpenAIThreadCreationOptions
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
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
    from openai.types.beta.assistant_tool import AssistantTool
    from openai.types.beta.threads.annotation import Annotation
    from openai.types.beta.threads.runs.tool_call import ToolCall
    from openai.types.file_object import FileObject

    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIAssistantBase(Agent):
    """OpenAI Assistant Base class."""

    ai_model_id: str
    client: AsyncOpenAI
    assistant: Assistant | None = None
    configuration: OpenAIServiceConfiguration
    definition: OpenAIAssistantDefinition
    polling_options: RunPollingOptions = Field(default_factory=RunPollingOptions)

    allowed_message_roles: ClassVar[list[str]] = [AuthorRole.USER, AuthorRole.ASSISTANT]
    polling_status: ClassVar[list[str]] = ["queued", "in_progress", "cancelling"]
    error_message_states: ClassVar[list[str]] = ["failed", "canceled", "expired"]

    _is_deleted: bool = False

    # region Assistant Initialization

    def __init__(
        self,
        ai_model_id: str,
        configuration: OpenAIServiceConfiguration,
        definition: OpenAIAssistantDefinition,
        client: AsyncOpenAI,
        service_id: str,
        kernel: "Kernel",
        *,
        id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAIAssistant Base.

        Args:
            ai_model_id (str): The AI model id. Defaults to None.
            configuration (OpenAIAssistantConfiguration): The configuration. Defaults to None.
            definition (OpenAIAssistantDefinition): The definition. Defaults to None.
            client (AsyncOpenAI): The client, either AsyncOpenAI or AsyncAzureOpenAI.
            service_id (str): The service id.
            kernel (Kernel): The kernel.
            id (str): The id. Defaults to None. (optional)
            name (str): The name. Defaults to None. (optional)
            description (str): The description. Defaults to None. (optional)
            default_headers (dict[str, str]): The default headers. Defaults to None. (optional)
            instructions (str): The instructions. Defaults to None. (optional)
            kwargs (Any): The keyword arguments.
        """
        args: dict[str, Any] = {}

        args = {
            "ai_model_id": ai_model_id,
            "client": client,
            "service_id": service_id,
            "instructions": instructions,
            "name": name,
            "description": description,
            "configuration": configuration,
            "definition": definition,
            "kernel": kernel,
        }

        if id is not None:
            args["id"] = id
        if kwargs:
            args.update(kwargs)

        super().__init__(**args)

    async def create_assistant(
        self,
    ) -> "Assistant":
        """Create the assistant."""
        kwargs: dict[str, Any] = {}

        tools = []
        if self.definition.enable_code_interpreter:
            tools.append({"type": "code_interpreter"})
        if self.definition.enable_file_search:
            tools.append({"type": "file_search"})

        kwargs["tools"] = tools if tools else None

        tool_resources = {}
        if self.definition.file_ids:
            tool_resources["code_interpreter"] = {"file_ids": self.definition.file_ids}
        if self.definition.vector_store_ids:
            tool_resources["file_search"] = {"vector_store_ids": self.definition.vector_store_ids}

        kwargs["tool_resources"] = tool_resources if tool_resources else None

        # Filter out None values to avoid passing them as kwargs
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        self.assistant = await self.client.beta.assistants.create(
            model=self.ai_model_id,
            instructions=self.instructions,
            name=self.name,
            **kwargs,
        )
        return self.assistant

    # endregion

    # region Agent Properties

    @property
    def metadata(self) -> dict[str, str]:
        """The metadata."""
        if self.assistant is None:
            raise AgentInitializationError("The assistant has not been created.")
        if not isinstance(self.assistant.metadata, dict):
            return {}
        return dict(self.assistant.metadata)

    @property
    def tools(self) -> list["AssistantTool"]:
        """The tools."""
        if self.assistant is None:
            raise AgentInitializationError("The assistant has not been created.")
        tools: list[AssistantTool] = []
        tools.extend(self.assistant.tools)
        tools.extend(
            [
                kernel_function_metadata_to_function_call_format(f)  # type: ignore
                for f in self.kernel.get_full_list_of_function_metadata()
            ]
        )
        return self.assistant.tools

    # endregion

    # region Agent Methods

    async def create_thread(self, thread_creation_settings: OpenAIThreadCreationOptions | None = None) -> str:
        """Create a thread.

        Args:
            thread_creation_settings (OpenAIThreadCreationSettings): The thread creation settings. Defaults to None.

        Returns:
            str: The thread id.
        """
        create_kwargs: dict[str, Any] = {}

        if thread_creation_settings:
            tool_resources = {}

            if thread_creation_settings.code_interpreter_file_ids:
                tool_resources["code_interpreter"] = {"file_ids": thread_creation_settings.code_interpreter_file_ids}

            if thread_creation_settings.vector_store_id:
                tool_resources["file_search"] = {"vector_store_ids": [thread_creation_settings.vector_store_id]}

            if tool_resources:
                create_kwargs["tool_resources"] = tool_resources

            if thread_creation_settings.messages:
                messages = []
                for message in thread_creation_settings.messages:
                    if message.role.value not in self.allowed_message_roles:
                        raise AgentExecutionError(
                            f"Invalid message role `{message.role.value}`. Allowed roles are {self.allowed_message_roles}."  # noqa: E501
                        )
                    message_contents = self._get_message_contents(message=message)
                    for content in message_contents:
                        messages.append({"role": message.role.value, "content": content})
                create_kwargs["messages"] = messages

            if thread_creation_settings.metadata:
                create_kwargs["metadata"] = thread_creation_settings.metadata

        thread = await self.client.beta.threads.create(**create_kwargs)
        return thread.id

    async def delete_thread(self, thread_id: str) -> None:
        """Delete a thread.

        Args:
            thread_id (str): The thread id.
        """
        await self.client.beta.threads.delete(thread_id)

    async def delete(self) -> bool:
        """Delete the assistant."""
        if not self._is_deleted and self.assistant:
            await self.client.beta.assistants.delete(self.assistant.id)
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

    async def get_thread_messages(self, thread_id: str) -> AsyncIterable[list[ChatMessageContent]]:
        """Get the messages for the specified thread.

        Args:
            thread_id (str): The thread id.

        Returns:
            list[ChatMessageContent]: The chat messages.
        """
        agent_names: dict[str, Any] = {}

        thread_messages = await self.client.beta.threads.messages.list(thread_id=thread_id, limit=100, order="desc")
        for message in thread_messages.data:
            role = AuthorRole(message.role)

            assistant_name = None
            if message.assistant_id and message.assistant_id not in agent_names:
                agent = await self.client.beta.assistants.retrieve(message.assistant_id)
                agent_names[message.assistant_id] = agent.name

            assistant_name = agent_names.get(message.assistant_id) if message.assistant_id else None
            contents: list[ChatMessageContent] = []
            for item in message.content:
                content: ChatMessageContent | ImageContent | None = None
                if item.type == "text":
                    content = ChatMessageContent(
                        role=role,
                        content=item.text.value,
                        name=assistant_name,
                    )
                    contents.append(content)
                    for annotation in item.text.annotations:
                        annotation_content = self._generate_annotation_content(annotation)
                        contents.append(annotation_content)  # type: ignore
                elif item.type == "image":
                    content = ImageContent(
                        role=role,
                        uri=item.image.url,
                        name=assistant_name,
                    )
                    contents.append(content)

            if contents:
                yield contents

    # region Agent Invoke Methods

    async def invoke(self, thread_id: str) -> AsyncIterable[ChatMessageContent]:
        """Invoke the chat assistant.

        Args:
            thread_id (str): The thread id.

        Yields:
            ChatMessageContent: The chat message content.
        """
        async for is_visible, content in self._invoke_internal(thread_id):
            if is_visible:
                yield content

    async def _invoke_internal(self, thread_id: str) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
        if not self.assistant:
            raise AgentInitializationError("The assistant has not been created.")

        if self._is_deleted:
            raise AgentInitializationError("The assistant has been deleted.")

        self._check_if_deleted()
        tools = self._get_tools()

        run = await self.client.beta.threads.runs.create(
            assistant_id=self.assistant.id,
            thread_id=thread_id,
            instructions=self.assistant.instructions,
            tools=tools,  # type: ignore
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
        )

    def _generate_annotation_content(self, annotation: "Annotation") -> AnnotationContent:
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
        contents: list[dict[str, Any]] = []
        for content in message.items:
            if isinstance(content, TextContent):
                contents.append({"type": "text", "text": content.text})
            elif isinstance(content, ImageContent) and content.uri:
                contents.append(content.to_dict())
        return contents

    def _generate_message_content(self, assistant_name: str, message: Message) -> ChatMessageContent:
        role = AuthorRole(message.role)

        content: ChatMessageContent = ChatMessageContent(role=role, name=assistant_name)  # type: ignore

        for item_content in message.content:
            if item_content.type == "text":
                content.items.append(
                    TextContent(
                        text=item_content.text.value,
                    )
                )
                for annotation in item_content.text.annotations:
                    content.items.append(self._generate_annotation_content(annotation))
            elif item_content.type == "image":
                content.items.append(
                    ImageContent(
                        uri=item_content.image.url,
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
        if self.definition and self.definition.enable_code_interpreter:
            tools.append({"type": "code_interpreter"})
        if self.definition and self.definition.enable_file_search:
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
