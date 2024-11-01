# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import ContentAdditionException


class StreamingTextContent(StreamingContentMixin, TextContent):
    """This represents streaming text response content.

    Args:
        choice_index: int - The index of the choice that generated this response.
        inner_content: Optional[Any] - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: Optional[str] - The id of the AI model that generated this response.
        metadata: Dict[str, Any] - Any metadata that should be attached to the response.
        text: Optional[str] - The text of the response.
        encoding: Optional[str] - The encoding of the text.

    Methods:
        __str__: Returns the text of the response.
        __bytes__: Returns the content of the response encoded in the encoding.
        __add__: Combines two StreamingTextContent instances.
    """

    def __bytes__(self) -> bytes:
        """Return the content of the response encoded in the encoding."""
        return self.text.encode(self.encoding if self.encoding else "utf-8") if self.text else b""

    def __add__(self, other: TextContent) -> "StreamingTextContent":
        """When combining two StreamingTextContent instances, the text fields are combined.

        The addition should follow these rules:
            1. The inner_content of the two will be combined. If they are not lists, they will be converted to lists.
            2. ai_model_id should be the same.
            3. encoding should be the same.
            4. choice_index should be the same.
            5. Metadata will be combined.
        """
        if isinstance(other, StreamingTextContent) and self.choice_index != other.choice_index:
            raise ContentAdditionException("Cannot add StreamingTextContent with different choice_index")
        if self.ai_model_id != other.ai_model_id:
            raise ContentAdditionException("Cannot add StreamingTextContent from different ai_model_id")
        if self.encoding != other.encoding:
            raise ContentAdditionException("Cannot add StreamingTextContent with different encoding")

        return StreamingTextContent(
            choice_index=self.choice_index,
            inner_content=self._merge_inner_contents(other.inner_content),
            ai_model_id=self.ai_model_id,
            metadata=self.metadata,
            text=(self.text or "") + (other.text or ""),
            encoding=self.encoding,
        )
