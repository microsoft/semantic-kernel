import logging
import sys

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents.agent import AgentThread
from semantic_kernel.contents.chat_message_content import ChatMessageContent

from copilot_studio.directline_client import DirectLineClient

# Logger setup
logger = logging.getLogger(__name__)


class CopilotAgentThread(AgentThread):
    """
    Thread implementation for Copilot Studio conversations via DirectLine API.
    Manages conversation IDs and watermarks for tracking conversation state.
    """

    def __init__(
        self,
        directline_client: DirectLineClient,
        conversation_id: str | None = None,
        watermark: str | None = None,
    ) -> None:
        """Initialize the Copilot Agent Thread.

        Args:
            directline_client: The DirectLine client for API communication.
            conversation_id: The conversation ID (optional).
            watermark: The watermark for tracking conversation state (optional).
        """
        super().__init__()
        self._directline_client = directline_client
        self._id = conversation_id
        self.watermark = watermark

    @override
    async def _create(self) -> str:
        """Starts the thread and returns the underlying Copilot Studio Agent conversation ID."""
        self._id = await self._directline_client.start_conversation()
        return self._id

    @override
    async def _delete(self) -> None:
        """Ends the current thread.

        This will only end the underlying DirectLine conversation but not delete it.
        """
        # DirectLine API does not provide a specific endpoint to delete conversations.
        pass

    @override
    async def _on_new_message(self, new_message: str | ChatMessageContent) -> None:
        """Called when a new message has been contributed to the chat."""
        # Not implemented for DirectLine
        pass
    
    async def update_watermark(self, watermark: str) -> None:
        """Update the watermark for the conversation.

        Args:
            watermark: The new watermark.
        """
        self.watermark = watermark