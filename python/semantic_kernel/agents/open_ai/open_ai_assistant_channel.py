# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.text_content_block import TextContentBlock

from semantic_kernel.agents.agent_channel import AgentChannel
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatError

if TYPE_CHECKING:
    from openai.resources.beta.threads.messages import Message
    from openai.types.beta.threads.annotation import Annotation

    from semantic_kernel.agents.agent import Agent


class OpenAIAssistantChannel(AgentChannel):
    """OpenAI Assistant Channel."""

    def __init__(self, client: AsyncOpenAI, thread_id: str, **data: Any) -> None:
        """Initialize the OpenAI Assistant Channel."""
        self.client = client
        self.thread_id = thread_id

    async def receive(self, history: list["ChatMessageContent"]) -> None:
        """Receive the conversation messages."""
        from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase

        for message in history:
            await OpenAIAssistantBase.create_chat_message(self.client, self.thread_id, message)

    async def invoke(self, agent: "Agent") -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Invoke the agent."""
        from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase

        if not isinstance(agent, OpenAIAssistantBase):
            raise AgentChatError(f"Agent is not of the expected type {type(OpenAIAssistantBase)}.")

        if agent._is_deleted:
            raise AgentChatError("Agent is deleted.")

        async for is_visible, message in agent._invoke_internal(thread_id=self.thread_id):
            yield is_visible, message

    async def get_history(self) -> AsyncIterable["ChatMessageContent"]:
        """Get the conversation history."""
        agent_names: dict[str, Any] = {}

        thread_messages = await self.client.beta.threads.messages.list(
            thread_id=self.thread_id, limit=100, order="desc"
        )
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

    def _generate_message_content(self, assistant_name: str, message: "Message") -> ChatMessageContent:
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
