# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, ClassVar, Iterable

from azure.ai.projects.models import CodeInterpreterTool, FileSearchTool, MessageAttachment, ToolDefinition

from semantic_kernel.contents.file_reference_content import FileReferenceContent

if TYPE_CHECKING:
    from semantic_kernel.contents import ChatMessageContent


class AzureAIAgentUtils:
    """AzureAI Agent Utility Methods."""

    tool_metadata: ClassVar[dict[str, ToolDefinition]] = {
        "file_search": FileSearchTool().definitions,
        "code_interpreter": CodeInterpreterTool().definitions,  # Assuming this is missing
    }

    @classmethod
    def get_metadata(cls, message: "ChatMessageContent") -> dict[str, str]:
        """Get the metadata for an agent message."""
        return {kvp.key: str(kvp.value) if kvp.value is not None else "" for kvp in (message.metadata or [])}

    @classmethod
    def get_attachments(cls, message: "ChatMessageContent") -> list[MessageAttachment]:
        """Get the attachments for an agent message.

        Args:
            message: The ChatMessageContent

        Returns:
            A list of MessageAttachment
        """
        return [
            MessageAttachment(file_content.file_id, list(cls._get_tool_definition(file_content.tools)))
            for file_content in message.items
            if isinstance(file_content, FileReferenceContent)
        ]

    @classmethod
    def _get_tool_definition(cls, tools: list[str]) -> Iterable[ToolDefinition]:
        if not tools:
            return iter([])

        for tool in tools:
            if tool_definition := cls.tool_metadata.get(tool):
                yield tool_definition
