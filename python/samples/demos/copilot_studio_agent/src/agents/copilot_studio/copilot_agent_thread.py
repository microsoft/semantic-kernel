# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from agents.copilot_studio.directline_client import DirectLineClient

from semantic_kernel.agents.agent import AgentThread
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException

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

        This will end the underlying DirectLine conversation but not delete it permanently
        from the service, as DirectLine API doesn't provide a specific endpoint to delete conversations.
        """
        if self._id:
            try:
                await self._directline_client.end_conversation(self._id)
                logger.debug(f"Conversation {self._id} has been ended")
            except Exception as e:
                logger.error(f"Failed to end conversation {self._id}: {str(e)}")

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
    
    async def post_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Post a message to the DirectLine conversation.
        
        Args:
            payload: The message payload to post.
            
        Returns:
            The response from the DirectLine API.
            
        Raises:
            AgentInvokeException: If posting the message fails or the thread ID is not set.
        """
        if not self._id:
            raise AgentInvokeException("Thread ID (conversation ID) is not set. Create the thread first.")
        
        try:
            return await self._directline_client.post_activity(self._id, payload)
        except Exception as e:
            logger.error(f"Failed to post message to thread {self._id}: {str(e)}")
            raise AgentInvokeException(f"Failed to post message: {str(e)}")
    
    async def get_messages(self) -> dict[str, Any]:
        """Get messages from the DirectLine conversation using the current watermark.
        
        Returns:
            The activities data from the DirectLine API.
            
        Raises:
            AgentInvokeException: If getting messages fails or the thread ID is not set.
        """
        if not self._id:
            raise AgentInvokeException("Thread ID (conversation ID) is not set. Create the thread first.")
        
        try:
            data = await self._directline_client.get_activities(self._id, self.watermark)
            watermark = data.get("watermark")
            if watermark:
                await self.update_watermark(watermark)
            return data
        except Exception as e:
            logger.error(f"Failed to get messages from thread {self._id}: {str(e)}")
            raise AgentInvokeException(f"Failed to get messages: {str(e)}")
