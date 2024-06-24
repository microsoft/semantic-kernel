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

## Cases

- 
- 

## Analysis

![](diagrams/agentchat-state-relationships.png)

## Options

- Direct Serialization: `JsonSerialize.Serialize(chat)`
- Serializer Raw: `AgentChatSerializer.Serialize(chat);`
- Serializer Encoded: `AgentChatSerializer.Serialize(chat);`

## Outcome

TBD