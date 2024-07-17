# Copyright (c) Microsoft. All rights reserved.

import asyncio
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any, ClassVar

from openai import AsyncOpenAI
from openai.resources.beta.assistants import Assistant
from pydantic import ValidationError

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.openai.open_ai_assistant_configuration import OpenAIAssistantConfiguration
from semantic_kernel.agents.openai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException

if TYPE_CHECKING:
    from openai.resources.beta.threads.messages import Message

    from semantic_kernel.kernel import Kernel


class OpenAIAssistantAgent(Agent):
    ai_model_id: str
    assistant: Assistant | None = None
    client: AsyncOpenAI | None = None
    config: OpenAIAssistantConfiguration | None = None
    definition: OpenAIAssistantDefinition | None = None

    allowed_message_roles: ClassVar[list[str]] = [AuthorRole.USER, AuthorRole.ASSISTANT]
    error_message_states: ClassVar[list[str]] = ["failed", "canceled", "expired"]

    _is_deleted: bool = False

    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        id: str | None = None,
        instructions: str | None = None,
        kernel: "Kernel | None" = None,
        configuration: OpenAIAssistantConfiguration | None = None,
        definition: OpenAIAssistantDefinition | None = None,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an OpenAIAssistant service."""
        if configuration is None:
            configuration = OpenAIAssistantConfiguration()

        if definition is None:
            definition = OpenAIAssistantDefinition()

        try:
            openai_settings = OpenAISettings.create(
                api_key=api_key,
                org_id=org_id,
                chat_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex

        if not client and not openai_settings.api_key:
            raise ServiceInitializationError("The OpenAI API key is required.")
        if not openai_settings.chat_model_id:
            raise ServiceInitializationError("The OpenAI model ID is required.")

        service_id = service_id or DEFAULT_SERVICE_NAME

        if client is None:
            client = AsyncOpenAI(
                api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
                organization=openai_settings.org_id,
            )

        args: dict[str, Any] = {
            "ai_model_id": openai_settings.chat_model_id,
            "service_id": service_id,
            "client": client,
            "name": name,
            "description": description,
            "instructions": instructions,
            "config": configuration,
            "definition": definition,
        }

        if id is not None:
            args["id"] = id
        if kernel is not None:
            args["kernel"] = kernel
        super().__init__(**args)

    async def create(
        self,
    ) -> Assistant:
        """Create the assistant."""
        self.assistant = await self.client.beta.assistants.create(
            model=self.ai_model_id,
            instructions=self.instructions,
            name=self.name,
        )
        return self.assistant

    @property
    def file_ids(self) -> list[str]:
        """The file ids."""
        return self.assistant.file_ids

    @property
    def metadata(self) -> dict[str, str]:
        """The metadata."""
        return self.assistant.metadata

    @property
    def tools(self) -> dict[str, str]:
        """The tools."""
        return self.assistant.tools

    # handle is_deleted

    async def create_thread(self) -> str:
        """Create a thread."""
        thread = await self.client.beta.threads.create()
        return thread.id

    async def delete_thread(self, thread_id: str) -> None:
        """Delete a thread."""
        await self.client.beta.threads.delete(thread_id)

    async def delete(self) -> bool:
        """Delete the assistant."""
        if not self._is_deleted:
            await self.client.beta.assistants.delete(self.assistant.id)
        return self._is_deleted

    async def invoke(self, thread_id: str) -> AsyncIterable[ChatMessageContent]:
        """Invoke the chat assistant."""
        # check if deleted
        if self._is_deleted:
            raise ServiceInitializationError("The assistant has been deleted.")

        # get tools
        tools: list[dict[str, str]] = []
        if self.definition.enable_code_interpreter:
            tools.append({"type": "code_interpreter"})
        if self.definition.enable_file_search:
            tools.append({"type": "file_search"})

        funcs = self.kernel.get_full_list_of_function_metadata()
        tools.extend([kernel_function_metadata_to_function_call_format(f) for f in funcs])

        run = await self.client.beta.threads.runs.create_and_poll(
            assistant_id=self.assistant.id,
            thread_id=thread_id,
            instructions=self.assistant.instructions,
            tools=tools,
        )

        if run.status in self.error_message_states:
            raise ServiceResponseException(f"Failed to create and run: `{run.status}` for agent {self.assistant.id}.")

        if run.status == "requires_action":
            # need to do function calling
            fccs: list[FunctionCallContent] = []
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                fcc = FunctionCallContent(
                    id=tool.id,
                    index=getattr(tool, "index", None),
                    name=tool.function.name,
                    arguments=tool.function.arguments,
                )
                fccs.append(fcc)

            chat_history = ChatHistory()

            results = []
            for function_call in fccs:
                result = await self.kernel.invoke_function_call(
                    function_call=function_call,
                    chat_history=chat_history,
                )
                results.append(result)

            tools_list: dict[str, str] = []
            for tool_call in chat_history.messages[0].items:
                tools_list.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": tool_call.result,
                    }
                )

            run = await self.client.beta.threads.runs.submit_tool_outputs(
                run_id=run.id, thread_id=thread_id, tool_outputs=tools_list
            )

            while run.status not in self.error_message_states:
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(run.id, thread_id=thread_id)
                if run.status == "completed":
                    break

        messages = await self.client.beta.threads.messages.list(thread_id=thread_id)
        assistant_messages = [next(message for message in messages.data if message.role == "assistant")]

        for message in assistant_messages:
            yield ChatMessageContent(content=message.content[0].text.value, role=message.role)

    async def add_chat_message(self, thread_id: str, message: ChatMessageContent) -> "Message":
        """Add a chat message."""
        if message.role not in self.allowed_message_roles:
            raise ServiceInitializationError(
                f"Invalid message role `{message.role}`. Allowed roles are {self.allowed_message_roles}."
            )
        return await self.client.beta.threads.messages.create(
            thread_id=thread_id, role=message.role, content=message.content
        )
