---
# These are optional elements. Feel free to remove any of them.
status: { accepted }
contact: { Tao Chen }
date: { 2024-09-18 }
deciders: { Tao Chen }
consulted: { Eduard van Valkenburg, Evan Mattson }
informed: { Eduard van Valkenburg, Evan Mattson, Ben Thomas }
---

# Streaming Contents for Token Usage Information (Semantic Kernel Python)

## Context and Problem Statement

Currently, `StreamingChatMessageContent` (inherits from `StreamingContentMixin`) in Semantic Kernel requires a choice index to be specified. This creates a limitation since the token usage information from **OpenAI's streaming chat completion** API will be returned in the last chunk where the choices field will be empty, which leads to an unknown choice index for the chunk. For more information, please refer to the [OpenAI API documentation](https://platform.openai.com/docs/api-reference/chat/create) and look for the `stream_options` field.

> The token usage information returned in the last chunk is the **total** token usage for the chat completion request regardless of the number of choices specified. That being said, there will be only one chunk containing the token usage information in the streaming response even when multiple choices are requested.

Our current data structure for `StreamingChatMessageContent`:

```Python
# semantic_kernel/content/streaming_chat_message_content.py
class StreamingChatMessageContent(ChatMessageContent, StreamingContentMixin):

# semantic_kernel/content/chat_message_content.py
class ChatMessageContent(KernelContent):
    content_type: Literal[ContentTypes.CHAT_MESSAGE_CONTENT] = Field(CHAT_MESSAGE_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = CHAT_MESSAGE_CONTENT_TAG
    role: AuthorRole
    name: str | None = None
    items: list[Annotated[ITEM_TYPES, Field(..., discriminator=DISCRIMINATOR_FIELD)]] = Field(default_factory=list)
    encoding: str | None = None
    finish_reason: FinishReason | None = None

# semantic_kernel/content/streaming_content_mixin.py
class StreamingContentMixin(KernelBaseModel, ABC):
    choice_index: int

# semantic_kernel/content/kernel_content.py
class KernelContent(KernelBaseModel, ABC):
    inner_content: Any | None = None
    ai_model_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

## Proposal 1

In non-streaming responses, the token usage is returned as part of the response from the model along with the choices that can be more than one. We then parse the choices into individual `ChatMessageContent`s, with each containing the token usage information, even though the token usage is for the entire response, not just the individual choice.

Considering the same strategy, all choices from the streaming response should contain the token usage information when they are eventually concatenated by their `choice_index`. Since we know the number of choices requested, we can perform the following steps:

1. Replicate the last chunk for each choice requested to create a list of `StreamingChatMessageContent`s, with the token usage information included in the metadata.
2. Assign a choice index to each replicated chunk, starting from 0.
3. Stream the replicated chunks in a list back to the client.

### Additional considerations

Currently, when two `StreamingChatMessageContent`s are "added" together, the metadata is not merged. We need to ensure that the metadata is merged when the chunks are concatenated. When there are conflicting metadata keys, the metadata from the second chunk should overwrite the metadata from the first chunk:

```Python
class StreamingChatMessageContent(ChatMessageContent, StreamingContentMixin):
    ...

    def __add__(self, other: "StreamingChatMessageContent") -> "StreamingChatMessageContent":
        ...

        return StreamingChatMessageContent(
            ...,
            metadata=self.metadata | other.metadata,
            ...
        )

    ...
```

### Risks

There are no breaking changes and known risks associated with this proposal.

## Proposal 2

We allow the choice index to be optional in the `StreamingContentMixin` class. This will allow the choice index to be `None` when the token usage information is returned in the last chunk. The choice index will be set to `None` in the last chunk, and the client can handle the token usage information accordingly.

```Python
# semantic_kernel/content/streaming_content_mixin.py
class StreamingContentMixin(KernelBaseModel, ABC):
    choice_index: int | None
```

This is a simpler solution compared to Proposal 1, and it is more in line with what the OpenAI API returns, that is the token usage is not associated with any specific choice.

### Risks

This is potentially a breaking change since the `choice_index` field is currently required. This approach also makes streaming content concatenation more complex since the choice index will need to be handled differently when it is `None`.

## Proposal 3

We will merge `ChatMessageContent` and `StreamingChatMessageContent` into a single class, `ChatMessageContent`, and mark `StreamingChatMessageContent` as deprecated. The `StreamingChatMessageContent` class will be removed in a future release. Then we apply the either [Proposal 1](#proposal-1) or [Proposal 2](#proposal-2) to the `ChatMessageContent` class to handle the token usage information.

This approach simplifies the codebase by removing the need for a separate class for streaming chat messages. The `ChatMessageContent` class will be able to handle both streaming and non-streaming chat messages.

```Python
# semantic_kernel/content/streaming_chat_message_content.py
@deprecated("StreamingChatMessageContent is deprecated. Use ChatMessageContent instead.")
class StreamingChatMessageContent(ChatMessageContent):
    pass

# semantic_kernel/content/chat_message_content.py
class ChatMessageContent(KernelContent):
    ...
    # Add the choice_index field to the ChatMessageContent class and make it optional
    choice_index: int | None

    # Add the __add__ method to merge the metadata when two ChatMessageContent instances are added together. This is currently an abstract method in the `StreamingContentMixin` class.
    def __add__(self, other: "ChatMessageContent") -> "ChatMessageContent":
        ...

        return ChatMessageContent(
            ...,
            choice_index=self.choice_index,
            ...
        )

    # Add the __bytes__ method to return the bytes representation of the ChatMessageContent instance. This is currently an abstract method in the `StreamingContentMixin` class.
    def __bytes__(self) -> bytes:
        ...
```

### Risks

We are unifying the returned data structure for streaming and non-streaming chat messages, which may lead to confusion for developers initially, especially if they are not aware of the deprecation of the `StreamingChatMessageContent` class, or they came from SK .Net. It may also create a sharper learning curve if developers started with Python but later move to .Net for production. This approach also introduces breaking changes to our AI connectors as the returned data type will be different.

> We will also need to update the `StreamingTextContent` and `TextContent` in a similar way too for this proposal.

## Proposal 4

Similar to [Proposal 3](#proposal-3), we will merge `ChatMessageContent` and `StreamingChatMessageContent` into a single class, `ChatMessageContent`, and mark `StreamingChatMessageContent` as deprecated. In addition, we will introduce another a new mixin called `ChatMessageContentConcatenationMixin` to handle the concatenation of two `ChatMessageContent` instances. Then we apply the either [Proposal 1](#proposal-1) or [Proposal 2](#proposal-2) to the `ChatMessageContent` class to handle the token usage information.

```Python
# semantic_kernel/content/streaming_chat_message_content.py
@deprecated("StreamingChatMessageContent is deprecated. Use ChatMessageContent instead.")
class StreamingChatMessageContent(ChatMessageContent):
    pass

# semantic_kernel/content/chat_message_content.py
class ChatMessageContent(KernelContent, ChatMessageContentConcatenationMixin):
    ...
    # Add the choice_index field to the ChatMessageContent class and make it optional
    choice_index: int | None

    # Add the __bytes__ method to return the bytes representation of the ChatMessageContent instance. This is currently an abstract method in the `StreamingContentMixin` class.
    def __bytes__(self) -> bytes:
        ...

class ChatMessageContentConcatenationMixin(KernelBaseModel, ABC):
    def __add__(self, other: "ChatMessageContent") -> "ChatMessageContent":
        ...
```

This approach separates the concerns of the `ChatMessageContent` class and the concatenation logic into two separate classes. This can help to keep the codebase clean and maintainable.

### Risks

Same as [Proposal 3](#proposal-3).

## Decision Outcome

To minimize the impact on customers and the existing codebase, we will go with [Proposal 1](#proposal-1) to handle the token usage information in the OpenAI streaming responses. This proposal is backward compatible and aligns with the current data structure for non-streaming responses. We will also ensure that the metadata is merged correctly when two `StreamingChatMessageContent` instances are concatenated. This approach also makes sure the token usage information will be associated to all choices in the streaming response.

[Proposal 3](#proposal-3) and [Proposal 4](#proposal-4) are still valid but perhaps premature at this stage as most services still return objects of different types for streaming and non-streaming responses. We will keep them in mind for future refactoring efforts.
