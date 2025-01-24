# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC, abstractmethod

if sys.version < "3.11":
    from typing_extensions import Self  # pragma: no cover
else:
    from typing import Self  # type: ignore # pragma: no cover

from pydantic import Field

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class ChatHistoryReducer(ChatHistory, ABC):
    """Defines a contract for reducing chat history."""

    target_count: int = Field(..., gt=0, description="Target message count.")
    threshold_count: int = Field(0, ge=0, description="Threshold count to avoid orphaning messages.")

    @abstractmethod
    async def reduce(self) -> Self | None:
        """Reduce the chat history in some way (e.g., truncate, summarize).

        Returns:
            A possibly shorter list of messages, or None if no change is needed.
        """
        ...
