from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


class CopilotContentType(str, Enum):
    TEXT = "text"
    ADAPTIVE_CARD = "adaptiveCard"
    SUGGESTED_ACTIONS = "suggestedActions"


class CopilotMessageContent(ChatMessageContent):
    """
    Extended ChatMessageContent that supports various content types from Copilot Studio
    including text, adaptive cards, and suggested actions.
    """
    copilot_content_type: CopilotContentType = Field(default=CopilotContentType.TEXT)
    adaptive_card: Optional[Dict[str, Any]] = Field(default=None)
    suggested_actions: Optional[List[Dict[str, Any]]] = Field(default=None)
    
    def __init__(
        self,
        role: AuthorRole,
        content: str = "",
        name: Optional[str] = None,
        copilot_content_type: CopilotContentType = CopilotContentType.TEXT,
        adaptive_card: Optional[Dict[str, Any]] = None,
        suggested_actions: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(
            role=role,
            content=content,
            name=name,
            **kwargs
        )
        
        self.copilot_content_type = copilot_content_type
        self.adaptive_card = adaptive_card
        self.suggested_actions = suggested_actions
            
        # Store rich content in metadata for preservation
        if adaptive_card:
            self.metadata["adaptive_card"] = adaptive_card
        if suggested_actions:
            self.metadata["suggested_actions"] = suggested_actions
            
    @classmethod
    def from_bot_activity(cls, activity: Dict[str, Any], name: str = None) -> "CopilotMessageContent":
        """
        Create a CopilotMessageContent instance from a DirectLine activity.
        
        Args:
            activity: The DirectLine activity object
            name: Optional name for the copilot agent sending the message
            
        Returns:
            A CopilotMessageContent instance with the appropriate content type
        """
        role = activity.get("from", {}).get("role", "assistant")
        if role == "bot":
            role = "assistant"
            
        # Get the base text content
        content = activity.get("text", "")
        name = name or activity.get("from", {}).get("name")
        
        # Check for suggested actions
        suggested_actions = activity.get("suggestedActions", {}).get("actions", [])
        
        # Check for adaptive card attachments
        attachments = activity.get("attachments", [])
        adaptive_card = None
        
        if attachments and attachments[0].get("contentType") == "application/vnd.microsoft.card.adaptive":
            adaptive_card = attachments[0].get("content", {})
            return cls(
                role=role,
                content=content,
                name=name,
                copilot_content_type=CopilotContentType.ADAPTIVE_CARD,
                adaptive_card=adaptive_card,
                suggested_actions=suggested_actions if suggested_actions else None,
            )
        elif suggested_actions:
            return cls(
                role=role,
                content=content,
                name=name,
                copilot_content_type=CopilotContentType.SUGGESTED_ACTIONS,
                suggested_actions=suggested_actions,
            )
        else:
            return cls(
                role=role,
                content=content,
                name=name,
                copilot_content_type=CopilotContentType.TEXT,
            )