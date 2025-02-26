# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from azure.ai.projects.models import (
    CodeInterpreterTool,
    FileSearchTool,
    MessageAttachment,
    MessageRole,
    ThreadMessageOptions,
    ToolDefinition,
)

from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.contents import ChatMessageContent

_T = TypeVar("_T", bound="AzureAIAgentUtils")


@experimental
class AzureAIAgentUtils:
    """AzureAI Agent Utility Methods."""

    tool_metadata: ClassVar[dict[str, Sequence[ToolDefinition]]] = {
        "file_search": FileSearchTool().definitions,
        "code_interpreter": CodeInterpreterTool().definitions,
    }

    @classmethod
    def get_thread_messages(cls: type[_T], messages: list["ChatMessageContent"]) -> Any:
        """Get the thread messages for an agent message."""
        if not messages:
            return None

        thread_messages: list[ThreadMessageOptions] = []

        for message in messages:
            if not message.content:
                continue

            thread_msg = ThreadMessageOptions(
                content=message.content,
                role=MessageRole.USER if message.role == AuthorRole.USER else MessageRole.AGENT,
                attachments=cls.get_attachments(message),
                metadata=cls.get_metadata(message) if message.metadata else None,
            )
            thread_messages.append(thread_msg)

        return thread_messages

    @classmethod
    def get_metadata(cls: type[_T], message: "ChatMessageContent") -> dict[str, str]:
        """Get the metadata for an agent message."""
        return {k: str(v) if v is not None else "" for k, v in (message.metadata or {}).items()}

    @classmethod
    def get_attachments(cls: type[_T], message: "ChatMessageContent") -> list[MessageAttachment]:
        """Get the attachments for an agent message.

        Args:
            message: The ChatMessageContent

        Returns:
            A list of MessageAttachment
        """
        return [
            MessageAttachment(
                file_id=file_content.file_id,
                tools=list(cls._get_tool_definition(file_content.tools)),  # type: ignore
                data_source=file_content.data_source if file_content.data_source else None,
            )
            for file_content in message.items
            if isinstance(file_content, FileReferenceContent)
        ]

    @classmethod
    def _get_tool_definition(cls: type[_T], tools: list[Any]) -> Iterable[ToolDefinition]:
        if not tools:
            return
        for tool in tools:
            if tool_definition := cls.tool_metadata.get(tool):
                yield from tool_definition
