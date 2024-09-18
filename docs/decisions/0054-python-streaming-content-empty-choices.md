---
# These are optional elements. Feel free to remove any of them.
status: { proposed }
contact: { Tao Chen }
date: { 2024-09-18 }
deciders: {}
consulted: {}
informed: {}
---

# Allow Empty Choices in Streaming Responses for Token Usage Information (Semantic Kernel Python)

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

This is potentially a breaking change since the `choice_index` field is currently required.

## Decision Outcome
