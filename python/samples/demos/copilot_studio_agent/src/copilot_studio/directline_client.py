import logging
from typing import Optional, Dict, Any, Mapping

import aiohttp

logger = logging.getLogger(__name__)

class DirectLineClient:
    """
    Manages DirectLine API interactions.
    Uses the bot secret directly for authentication rather than managing tokens.
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
        self._session: Optional[aiohttp.ClientSession] = None

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

    async def close(self) -> None:
        """
        Close the aiohttp session.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("DirectLine session closed")
    
    async def post_activity(self, conversation_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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
        
        async with session.post(activities_url, json=payload) as resp:
            if resp.status != 200:
                logger.error("Failed to post activity. Status: %s", resp.status)
                raise Exception(f"Failed to post activity. Status: {resp.status}")
            
            return await resp.json()
    
    async def get_activities(self, conversation_id: str, watermark: Optional[str] = None) -> Dict[str, Any]:
        """
        Get activities from a DirectLine conversation.
        
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
            
        logger.debug(f"Polling activities at {activities_url}")
        
        async with session.get(activities_url) as resp:
            if resp.status != 200:
                logger.error("Error polling activities. Status: %s", resp.status)
                raise Exception(f"Error polling activities. Status: {resp.status}")
            
            return await resp.json()
            
    async def start_conversation(self) -> str:
        """
        Start a new DirectLine conversation.
        Uses the bot secret directly to start the conversation.
        
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