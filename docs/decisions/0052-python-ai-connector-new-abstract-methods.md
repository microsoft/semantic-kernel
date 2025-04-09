---
# These are optional elements. Feel free to remove any of them.
status: { accepted }
contact: { Tao Chen }
date: { 2024-09-03 }
deciders: { Eduard van Valkenburg, Ben Thomas }
consulted: { Eduard van Valkenburg }
informed: { Eduard van Valkenburg, Ben Thomas }
---

# New abstract methods in `ChatCompletionClientBase` and `TextCompletionClientBase` (Semantic Kernel Python)

## Context and Problem Statement

The ChatCompletionClientBase class currently contains two abstract methods, namely `get_chat_message_contents` and `get_streaming_chat_message_contents`. These methods offer standardized interfaces for clients to engage with various models.

> We will focus on `ChatCompletionClientBase` in this ADR but `TextCompletionClientBase` will be having a similar structure.

With the introduction of function calling to many models, Semantic Kernel has implemented an amazing feature known as `auto function invocation`. This feature relieves developers from the burden of manually invoking the functions requested by the models, making the development process much smoother.

Auto function invocation can cause a side effect where a single call to get_chat_message_contents or get_streaming_chat_message_contents may result in multiple calls to the model. However, this presents an excellent opportunity for us to introduce another layer of abstraction that is solely responsible for making a single call to the model.

## Benefits

- To simplify the implementation, we can include a default implementation of `get_chat_message_contents` and `get_streaming_chat_message_contents`.
- We can introduce common interfaces for tracing individual model calls, which can improve the overall monitoring and management of the system.
- By introducing this layer of abstraction, it becomes more efficient to add new AI connectors to the system.

## Details

### Two new abstract methods

> Revision: In order to not break existing customers who have implemented their own AI connectors, these two methods are not decorated with the `@abstractmethod` decorator, but instead throw an exception if they are not implemented in the built-in AI connectors.

```python
async def _inner_get_chat_message_content(
    self,
    chat_history: ChatHistory,
    settings: PromptExecutionSettings
) -> list[ChatMessageContent]:
    raise NotImplementedError
```

```python
async def _inner_get_streaming_chat_message_content(
    self,
    chat_history: ChatHistory,
    settings: PromptExecutionSettings
) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
    raise NotImplementedError
```

### A new `ClassVar[bool]` variable in `ChatCompletionClientBase` to indicate whether a connector supports function calling

This class variable will be overridden in derived classes and be used in the default implementations of `get_chat_message_contents` and `get_streaming_chat_message_contents`.

```python
class ChatCompletionClientBase(AIServiceClientBase, ABC):
    """Base class for chat completion AI services."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False
    ...
```

```python
class MockChatCompletionThatSupportsFunctionCalling(ChatCompletionClientBase):

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    @override
    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        if not self.SUPPORTS_FUNCTION_CALLING:
            return ...
        ...
```
