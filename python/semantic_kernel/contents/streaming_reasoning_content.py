# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.contents.reasoning_content import ReasoningContent
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.exceptions import ContentAdditionException


class StreamingReasoningContent(StreamingContentMixin, ReasoningContent):
    """This represents streaming reasoning response content.

    Args:
        choice_index: int - The index of the choice that generated this response.
        inner_content: Optional[Any] - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: Optional[str] - The id of the AI model that generated this response.
        metadata: Dict[str, Any] - Any metadata that should be attached to the response.
        text: Optional[str] - The reasoning text of the response.

    Methods:
        __str__: Returns the text of the response.
        __bytes__: Returns the content of the response encoded as UTF-8.
        __add__: Combines two StreamingReasoningContent instances.
    """

    def __bytes__(self) -> bytes:
        """Return the content of the response encoded as UTF-8."""
        return self.text.encode("utf-8") if self.text else b""

    def __add__(self, other: ReasoningContent) -> "StreamingReasoningContent":
        """When combining two StreamingReasoningContent instances, the text fields are combined.

        The addition should follow these rules:
            1. The inner_content of the two will be combined. If they are not lists, they will be converted to lists.
            2. ai_model_id should be the same.
            3. choice_index should be the same.
            4. Metadata will be combined.
        """
        if isinstance(other, StreamingReasoningContent) and self.choice_index != other.choice_index:
            raise ContentAdditionException("Cannot add StreamingReasoningContent with different choice_index")
        if self.ai_model_id != other.ai_model_id:
            raise ContentAdditionException("Cannot add StreamingReasoningContent from different ai_model_id")

        return StreamingReasoningContent(
            choice_index=self.choice_index,
            inner_content=self._merge_inner_contents(other.inner_content),
            ai_model_id=self.ai_model_id,
            metadata={**self.metadata, **(other.metadata or {})},
            text=(self.text or "") + (other.text or ""),
        )
