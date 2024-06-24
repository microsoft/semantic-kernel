---
status: proposed
contact: crickman
date: 2024-06-24
deciders: bentho, matthewbolanos
---

# Agent-Chat Serialization / Deserialization

## Context and Problem Statement

{Describe the context and problem statement, e.g., in free form using two to three sentences or in the form of an illustrative story.
You may want to articulate the problem in form of a question and add links to collaboration boards or issue management systems.}

#### Non-Goals
- Manage agent definitions
- Manage secrets or api-keys

## Cases
- Same agents present in chat
- Subset of agents present in chat
- Additional agents present in chat
- No agents present in chat
- Chat has history or channels already

## Analysis

![AgentChat Relationships](diagrams/agentchat-relationships.png)

![AgentChat State](diagrams/agentchat-state.png)

```
internal sealed class AgentChatState
{
    public ChatHistory History { get; set; }

    /// <summary>
    /// %%%
    /// </summary>
    public IEnumerable<AgentChannelState> Channels { get; set; } = [];
}
```

## Options

- Direct Serialization: `JsonSerialize.Serialize(chat)`
- Serializer Raw: `AgentChatSerializer.Serialize(chat);`
- Serializer Encoded: `AgentChatSerializer.Serialize(chat);`

## Outcome

TBD