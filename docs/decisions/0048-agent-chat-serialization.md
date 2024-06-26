---
status: proposed
contact: crickman
date: 2024-06-24
deciders: bentho, matthewbolanos
---

# `AgentChat` Serialization / Deserialization

## Context and Problem Statement
Users of the _Agent Framework_ are unable to store and later retrieve conversation state when using an `AgentChat` to coordinate `Agent` interactions.  This limits the ability for an agent conversation to single use as it must be maintained with memory of the process that initiated the conversation.

Formalizing a mechanism that supports serialization and deserialization of any `AgentChat` class provides an avenue to capture and restore state across multiple sessions as well as compute boundaries.

#### Non-Goals
- **Manage agent definition:** An `Agent` definition shall not be captured as part of the conversation state.  `Agent` instances will not be produced when deserializing the state of an `AgentChat` class.
- **Manage secrets or api-keys:** Secrets / api-keys are required when producing an `Agent` instance.  Managing this type of sensitive data is out-of-scope due to security considerations.


## Cases
When restoring an `AgentChat`, the application must also re-create the `Agent` instances participating in the chat (outside of the control of the deserialization process).  This creates the opportunity for the following cases:

#### 1. **Equivalent:** All of the original agent types (channels) available in the restored chat.
This shall result in a full-fidelity restoration of of the original chat.

|Source Chat|Target Chat|
|---|---|
|`ChatCompletionAgent`|`ChatCompletionAgent`|
|`OpenAIAssistantAgent`|`OpenAIAssistantAgent`|
|`ChatCompletionAgent` & `OpenAIAssistantAgent`|`ChatCompletionAgent` & `OpenAIAssistantAgent`|

#### 2. **Enhanced:** Additional original agent types (channels) available in the restored chat.
This shall also result in a full-fidelity restoration of of the original chat.
Any new agent type (channel) will synchronize to the chat once restored (identical to adding a new agent type to a chat that is progress).

|Source Chat|Target Chat|
|---|---|
|`ChatCompletionAgent`|`ChatCompletionAgent` & `OpenAIAssistantAgent`|
|`OpenAIAssistantAgent`|`ChatCompletionAgent` & `OpenAIAssistantAgent`|

#### 3. **Reduced:** A subset of original agent types (channels) available in the restored chat.
This shall also result in a full-fidelity restoration of of the original chat to the available channels.  Introduction of a missing agent type (channel) post restoration will
synchronize the channel to the current chat (identical to adding a new agent type to a chat that is progress).

|Source Chat|Target Chat|
|---|---|
|`ChatCompletionAgent` & `OpenAIAssistantAgent`|`ChatCompletionAgent`|
|`ChatCompletionAgent` & `OpenAIAssistantAgent`|`OpenAIAssistantAgent`|

#### 4. **Empty:** No agents available in the restored chat.
This shall result in an immediate exception (fail-fast) in order to strongly indicate that
the chat has not been restored.  The chat may have agents added in order to attempt a successful restoration, or utilized on its own.  That is, the `AgentChat` instance isn't invalidated.

#### 5. **Invalid:** Chat has already developed history or channels state.
This shall result in an immediate exception (fail-fast) in order to strongly indicate that
the chat has not been restored.  The chat may continue to be utilized as the `AgentChat` instance isn't invalidated.

#### Notes:

> The number or definitions of  `Agents` instances has no consequence on the ability to restore `AgentChat` state.

> Once restored, additional `Agent` instances may join the `AgentChat`, no different from any `AgentChat` instance.

## Analysis
The relationships between any `AgentChat`, the `Agent` instances participating in the conversation, and the associated `AgentChannel` conduits are illustrated in the following diagram:

![AgentChat Relationships](diagrams/agentchat-relationships.png)

While an `AgentChat` manages a primary `ChatHistory`, each `AgentChannel` manages how that history is adapted to the specific `Agent` modality.  For instance, an `AgentChanel` for an `Agent` based on the Open AI Assistant API tracks the associated _thread-id_.  Whereas a `ChatCompletionAgent` manages an adpated `ChatHistory` instance of its own.

This implies that logically the `AgentChat` state must retain the primary `ChatHistory` in addition to the appropriate state for each `AgentChannel`:

![AgentChat State](diagrams/agentchat-state.png)


## Options

#### 1. JSON Serializer:

A dominant serialization pattern is to use the dotnet `JsonSerializer`.  This is the approach relied upon by the _Semantic Kernel_ content types.

**Serialize:**
```c#
Agent agent1 = ...;
Agent agent2 = ...;
AgentGroupChat chat = new (agent1, agent2);

string chatState = JsonSerializer.Serialize(chat);
```

**Deserialize:**
```c#
AgentGroupChat chat = JsonSerializer.Deserialize<AgentGroupChat>(chatState);
```

**Pro:**
- Doesn't require knowledge of a serialization pattern specific to the _Agent Framework_.

**Con:**
- Both `AgentChat` nor `AgentChannel` are designed as a service classes, not _data transfer objects_ (DTO's).  Implies disruptive refactoring. (Think: complete re-write)
- Requires caller to address complexity to support serialization of unknown `AgentChannel` and `AgentChat` subclasses.
- Limits ability to post process when restoring chat (e.g. channel synchronization).
- Absence of `Agent` instances in deserialization interferes with ability to restore any `AgentChannel`.


#### 2. `AgentChat` Serializer: 

Introducing a serializer with specific knowledge of `AgentChat` contracts enables the ability to streamline serialization and deserialization.

```c#
public static class AgentChatSerializer
{
    public static async Task SerializeAsync<TChat>(TChat chat, Stream stream)
        where TChat : AgentChat;

    public static async Task DeserializeAsync<TChat>(TChat chat, Stream stream)
        where TChat : AgentChat;
}
```

**Pro:**
- Able to clearly defines the chat-state, separate from the chat _service_ requirements.
- Support any `AgentChat` and `AgentChannel` subclass.
- Ability to support post processing when restoring chat (e.g. channel synchronization).
- Allows any `AgentChat` to be propertly initialized prior to deserialization.

**Con:**
- Require knowledge of a serialization pattern specific to the _Agent Framework_.
- Channel state is escaped.

**Serialize:**
```c#
Agent agent1 = ...;
Agent agent2 = ...;
AgentGroupChat chat = new (agent1, agent2);

await chat.InvokeAsync();

async using Stream stream = ...; // Initialize the serialization stream
AgentChatSerializer.Serialize(chat, stream);
```

**Deserialize:**
```c#
Agent agent1 = ...;
Agent agent2 = ...;
AgentGroupChat chat = new (agent1, agent2);

async using Stream stream = ...; // Initialize the deserialization stream
AgentChatSerializer.Deserialize(chat, stream);

await chat.InvokeAsync();
```

**Serialized State:**
```json
{
    "history": [
        { "role": "user", "items": [ /* ... */ ] }, // Serialized ChatMessageContent
        { "role": "assistant", "name": "John", "items": [ /* ... */ ] }, // Serialized ChatMessageContent
        // ...
    ],
    "channels": [
        {
            "channelkey": "Vdx37EnWT9BS+kkCkEgFCg9uHvHNw1+hXMA4sgNMKs4=",
            "channelstate": "...",  // Serialized state for an AgentChannel
        },
        // ...
    ]
}
```


#### 3. `AgentChat` Serializer Encoded

This option is identical to the second option; however, each discrete state is encoded to discourage modification / manipulation of the captured state.

**Pro:**
- Discourages ability to inspect and modify.
- Still able to decode to inspect and modify.
- Eliminates need to escape channel state.

**Con:**
- Discourages ability to inspect and modify.
- Still able to decode to inspect and modify.

**Serialized State:**
```json
{
    "history": "VGhpcyBpcyB0aGUgcHJpbWFyeSBjaGF0IGhpc3Rvcnkg...",
    "channels": [
        {
            "channelkey": "Vdx37EnWT9BS+kkCkEgFCg9uHvHNw1+hXMA4sgNMKs4=",
            "channelstate": "VGhpcyBpcyBhZ2VudCBjaGFubmVsIHN0YXRlIGV4YW1wbG..."
        },
        // ...
    ]
}
```


## Outcome

TBD