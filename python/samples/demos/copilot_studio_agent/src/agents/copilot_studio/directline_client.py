# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class DirectLineClient:
    """
    Handles Direct Line API interactions for Copilot Studio agents.
    Provides methods for authentication, starting conversations, posting activities,
    and polling responses, including support for watermark-based activity retrieval.
    """

    def __init__(
        self,
        directline_endpoint: str,
        copilot_agent_secret: str,
    ) -> None:
        """
        Initialize the DirectLine Client.

        Args:
            directline_endpoint: The endpoint for the DirectLine API.
            copilot_agent_secret: The secret used to authenticate with DirectLine API.

        """
        self.directline_endpoint = directline_endpoint
        self.copilot_agent_secret = copilot_agent_secret
        self._session: aiohttp.ClientSession | None = None

    async def get_session(self) -> aiohttp.ClientSession:
        """
        Get an authenticated aiohttp ClientSession using the bot secret.
        Creates a new session if one doesn't exist already.

        Returns:
            An authenticated aiohttp ClientSession.
        """
        # Create a session with the bot secret for authorization
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.copilot_agent_secret}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(headers=headers)

        return self._session

    async def start_conversation(self) -> str:
        """
        Start a new DirectLine conversation.

        Returns:
            The conversation ID.

        Raises:
            Exception: If starting the conversation fails.
        """
        # Use the session with the bot secret for authorization
        session = await self.get_session()

        async with session.post(f"{self.directline_endpoint}/conversations") as resp:
            if resp.status not in (200, 201):
                raise Exception(f"Failed to create DirectLine conversation. Status: {resp.status}")

            data = await resp.json()
            conversation_id = data.get("conversationId")

            if not conversation_id:
                logger.error("Conversation creation response missing conversationId: %s", data)
                raise Exception("No conversation ID received from conversation creation.")

            logger.debug(f"Created conversation {conversation_id}")

            return conversation_id

    async def post_activity(self, conversation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Post an activity to a DirectLine conversation.

        Args:
            conversation_id: The conversation ID.
            payload: The activity payload to post.

        Returns:
            The response from the API.

        Raises:
            Exception: If posting the activity fails.
        """
        session = await self.get_session()
        activities_url = f"{self.directline_endpoint}/conversations/{conversation_id}/activities"

        logger.debug(f"Posting activity to {activities_url}")
        async with session.post(activities_url, json=payload) as resp:
            if resp.status != 200:
                logger.error("Failed to post activity. Status: %s", resp.status)
                raise Exception(f"Failed to post activity. Status: {resp.status}")

            return await resp.json()

    async def get_activities(self, conversation_id: str, watermark: str | None = None) -> dict[str, Any]:
        """
        Get activities from a DirectLine conversation.
        Use watermark to retrieve new activities since the last retrieved activity.

        Args:
            conversation_id: The conversation ID.
            watermark: The watermark for retrieving new activities.

        Returns:
            The activities data.

        Raises:
            Exception: If retrieving activities fails.
        """
        session = await self.get_session()
        activities_url = f"{self.directline_endpoint}/conversations/{conversation_id}/activities"

        if watermark:
            activities_url = f"{activities_url}?watermark={watermark}"

        async with session.get(activities_url) as resp:
            if resp.status != 200:
                logger.error("Error polling activities. Status: %s", resp.status)
                raise Exception(f"Error polling activities. Status: {resp.status}")

            return await resp.json()

    async def end_conversation(self, conversation_id: str, user_id: str = "user1") -> dict[str, Any]:
        """
        End a DirectLine conversation by sending an endOfConversation activity.

        Args:
            conversation_id: The conversation ID to end.
            user_id: The user ID to use in the 'from' field (defaults to "user1").

        Returns:
            The response from the API.

        Raises:
            Exception: If ending the conversation fails.
        """
        payload = {"type": "endOfConversation", "from": {"id": user_id}}

        session = await self.get_session()
        activities_url = f"{self.directline_endpoint}/conversations/{conversation_id}/activities"

        async with session.post(activities_url, json=payload) as resp:
            if resp.status != 200:
                logger.error("Failed to end conversation. Status: %s", resp.status)
                raise Exception(f"Failed to end conversation. Status: {resp.status}")

            logger.debug(f"Successfully ended conversation {conversation_id}")
            return await resp.json()

    async def close(self) -> None:
        """
        Close the aiohttp session.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("DirectLine session closed")
