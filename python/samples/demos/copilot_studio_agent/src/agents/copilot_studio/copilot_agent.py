import asyncio
import logging
import sys
from collections.abc import AsyncIterable
from typing import Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from agents.copilot_studio.copilot_agent_channel import CopilotStudioAgentChannel
from agents.copilot_studio.copilot_agent_thread import CopilotAgentThread
from agents.copilot_studio.copilot_message_content import CopilotMessageContent
from agents.copilot_studio.directline_client import DirectLineClient

from semantic_kernel.agents import Agent
from semantic_kernel.agents.agent import AgentResponseItem, AgentThread
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)

logger: logging.Logger = logging.getLogger(__name__)


class CopilotAgent(Agent):
    """
    An agent that facilitates communication with a Microsoft Copilot Studio bot via the Direct Line API.  
    It serializes user inputs into Direct Line payloads, handles asynchronous response polling, and transforms bot activities into structured message content.  
    Conversation state such as conversation ID and watermark is externally managed by CopilotAgentThread.
    """    
    directline_client: DirectLineClient | None = None

    channel_type: ClassVar[type[AgentChannel]] = CopilotStudioAgentChannel

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        directline_client: DirectLineClient,
    ) -> None:
        """
        Initialize the CopilotAgent.
        """
        super().__init__(id=id, name=name, description=description)
        self.directline_client = directline_client
        
    @override
    def get_channel_keys(self) -> list[str]:
        """
        Override to return agent ID instead of channel_type for Copilot agents.
        
        This is particularly important for CopilotAgent because each agent instance 
        maintains its own conversation with a unique thread ID in the DirectLine API.
        Without this override, multiple CopilotAgent instances in a group chat would 
        share the same channel, causing thread ID conflicts and message routing issues.
        
        Returns:
            A list containing the agent ID as the unique channel key, ensuring each 
            CopilotAgent gets its own dedicated channel and thread.
        """
        return [self.id]

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        thread: AgentThread | None = None,
        **kwargs,
    ) -> AgentResponseItem[CopilotMessageContent]:
        """
        Get a response from the agent on a thread.

        Args:
            messages: The input chat message content either as a string, ChatMessageContent or
                a list of strings or ChatMessageContent.
            thread: The thread to use for the agent.
            kwargs: Additional keyword arguments.

        Returns:
            AgentResponseItem[ChatMessageContent]: The response from the agent.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: CopilotAgentThread(directline_client=self.directline_client),
            expected_type=CopilotAgentThread,
        )
        assert thread.id is not None  # nosec

        response_items = []
        async for response_item in self.invoke(
            messages=messages,
            thread=thread,
            **kwargs,
        ):
            response_items.append(response_item)

        if not response_items:
            raise AgentInvokeException("No response messages were returned from the agent.")

        return response_items[-1]

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        thread: AgentThread | None = None,
        message_data: dict[str, Any] | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[CopilotMessageContent]]:
        """Invoke the agent on the specified thread.

        Args:
            messages: The input chat message content either as a string, ChatMessageContent or
                a list of strings or ChatMessageContent.
            thread: The thread to use for the agent.
            message_data: Optional dict that will be sent as the "value" field in the payload
                for adaptive card responses.
            kwargs: Additional keyword arguments.

        Yields:
            AgentResponseItem[ChatMessageContent]: The response from the agent.
        """
        logger.debug("Received messages: %s", messages)
        if not isinstance(messages, str) and not isinstance(messages, ChatMessageContent):
            raise AgentInvokeException("Messages must be a string or a ChatMessageContent for Copilot Agent.")

        # Ensure DirectLine client is initialized
        if self.directline_client is None:
            raise AgentInvokeException("DirectLine client is not initialized.")
        
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: CopilotAgentThread(directline_client=self.directline_client),
            expected_type=CopilotAgentThread,
        )
        assert thread.id is not None  # nosec

        normalized_message = ChatMessageContent(role=AuthorRole.USER, content=messages) if isinstance(messages, str) else messages

        payload = self._build_payload(normalized_message, message_data, thread.id)
        response_data = await self._send_message(payload, thread)
        if response_data is None or "activities" not in response_data:
            raise AgentInvokeException(
                f"Invalid response from DirectLine Bot.\n{response_data}"
            )

        # Process DirectLine activities and convert them to appropriate message content
        for activity in response_data["activities"]:
            if (
                activity.get("type") != "message"
                or activity.get("from", {}).get("id") == "user"
            ):
                continue
            
            # Create a CopilotMessageContent instance from the activity
            message = CopilotMessageContent.from_bot_activity(activity, name=self.name)

            logger.debug("Response message: %s", message.content)
            
            yield AgentResponseItem(message=message, thread=thread)

    def _build_payload(
        self,
        message: ChatMessageContent,
        message_data: dict[str, Any] | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Build the message payload for the DirectLine Bot.

        Args:
            message: The message content to send.
            message_data: Optional dict that will be sent as the "value" field in the payload
                for adaptive card responses.
            thread_id: The thread ID (conversation ID).

        Returns:
            A dictionary representing the payload to be sent to the DirectLine Bot.
        """
        payload = {
            "type": "message",
            "from": {"id": "user"},
        }
        
        if message_data and "adaptive_card_response" in message_data:
            payload["value"] = message_data["adaptive_card_response"]
        else:
            payload["text"] = message.content
            
        payload["conversationId"] = thread_id
        return payload

    async def _send_message(self, payload: dict[str, Any], thread: CopilotAgentThread) -> dict[str, Any] | None:
        """
        Post the payload to the conversation and poll for responses.
        """
        if self.directline_client is None:
            raise AgentInvokeException("DirectLine client is not initialized.")

        # Post the message payload
        await thread.post_message(payload)

        # Poll for new activities using watermark until DynamicPlanFinished event is found
        finished = False
        collected_data = None
        while not finished:
            data = await thread.get_messages()
            activities = data.get("activities", [])
            
            # Check for either DynamicPlanFinished event or message from bot
            if any(
                (
                    activity.get("type") == "event"
                    and activity.get("name") == "DynamicPlanFinished"
                )
                or
                (
                    activity.get("type") == "message"
                    and activity.get("from", {}).get("role") == "bot"
                )
                for activity in activities
            ):
                collected_data = data
                finished = True
                break
            
            await asyncio.sleep(1)

        return collected_data

    async def close(self) -> None:
        """
        Clean up resources.
        """
        if self.directline_client:
            await self.directline_client.close()

    @trace_agent_invocation
    @override
    async def invoke_stream(self, *args, **kwargs):
        return super().invoke_stream(*args, **kwargs)
    
    async def create_channel(self, thread_id: str | None = None) -> AgentChannel:
        """Create a Copilot Agent channel.

        Args:
            thread_id: The ID of the thread. If None, a new thread will be created.

        Returns:
            An instance of AgentChannel.
        """
        from agents.copilot_studio.copilot_agent_channel import CopilotStudioAgentChannel

        if self.directline_client is None:
            raise AgentInvokeException("DirectLine client is not initialized.")
            
        thread = CopilotAgentThread(directline_client=self.directline_client, conversation_id=thread_id)

        if thread.id is None:
            await thread.create()

        return CopilotStudioAgentChannel(thread=thread)
