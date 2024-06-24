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
- Same agents present in chat
- Subset of agents present in chat
- Additional agents present in chat
- No agents present in chat
- Chat has history or channels already

## Analysis

![AgentChat Relationships](diagrams/agentchat-relationships.png)

![AgentChat State](diagrams/agentchat-state.png)


## Options

- Direct Serialization: `JsonSerialize.Serialize(chat)`
- Serializer Raw: `AgentChatSerializer.Serialize(chat);`
- Serializer Encoded: `AgentChatSerializer.Serialize(chat);`

## Outcome

TBD