---
# These are optional elements. Feel free to remove any of them.
status: accepted
date: 2023-10-27
contact: SergeyMenshykh
deciders: markwallace, mabolan
consulted:
informed:
---
# Mapping of prompt syntax to completion service model

## Context and Problem Statement
Today, SK runs all prompts using the text completion service by simply passing the rendered prompt as is, without any modifications, directly to a configured text completion service/connector. With the addition of new chat completion prompt and potentially other prompt types, such as image, on the horizon, we need a way to map completion-specific prompt syntax to the corresponding completion service data model.

For example, [the chat completion syntax](https://github.com/microsoft/semantic-kernel/blob/main/docs/decisions/0014-chat-completion-roles-in-prompt.md) in chat completion prompts:
```xml
<message role="system">
    You are a creative assistant helping individuals and businesses with their innovative projects.
</message>
<message role="user">
    I want to brainstorm the idea of {{$input}}
</message>
```
should be mapped to an instance of the [ChatHistory](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/ChatHistory.cs) class with two chat messages:

```csharp
var messages = new ChatHistory();
messages.Add(new ChatMessage(new AuthorRole("system"), "You are a creative assistant helping individuals and businesses with their innovative projects."));
messages.Add(new ChatMessage(new AuthorRole("user"), "I want to brainstorm the idea of {{$input}}"));
```

This ADR outlines potential options for the location of the prompt syntax mapping functionality.

## Considered Options
**1. Completion connector classes.** This option proposes to have the completion connector classes responsible for the `prompt syntax -> completion service data model` mapping. The decision regarding whether this mapping functionality will be implemented in the connector classes themselves or delegated to mapper classes should be made during the implementation phase and is out of the scope of this ADR.

Pros:
 - The `SemanticFunction` won't need to change to support the mapping of a new prompt syntax when new completion type connectors (audio, video, etc.) are added.
 
 - Prompts can be run by
    - Kernel.RunAsync 
    - Completion connectors

Cons:
 - Every new completion connector, whether of an existing type or a new type, will have to implement the mapping functionality

**2. The SemanticFunction class.** This option proposes that the `SemanticFunction` class be responsible for the mapping. Similar to the previous option, the exact location of this functionality (whether in the `SemanticFunction` class or in the mapper classes) should be decided during the implementation phase.

Pros:
 - New connectors of a new type or existing ones don't have to implement the mapping functionality

Cons:
 - The `SemanticFunction` class has to be changed every time a new completion type needs to be supported by SK
 - Prompts can be run by Kernel.RunAsync method only.

## Decision Outcome
It was agreed to go with the option 1 - `1. Completion connector classes` since it a more flexible solution and allows adding new connectors without modifying the `SemanticFunction` class.