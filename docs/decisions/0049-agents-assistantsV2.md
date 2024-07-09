
# Agent Framework - Assistant V2 Migration

## Context and Problem Statement

TBD

### Open Issues
- **Tool Constraints:** In Progress
- **Streaming:** To be addressed as a discrete feature
- **Polling:** Associate with execution settings?

## Design

### Configuration Classes

TBD

#### Service Configuration

TBD

<p align="center">
<kbd><img src="diagrams/assistant-serviceconfig.png"  style="width: 360pt;"></kbd>
</p>

#### Assistant Definition

TBD

<p align="center">
<kbd><img src="diagrams/assistant-definition.png"  style="width: 360pt;"></kbd>
</p>

#### Assistant Invocation Settings

TBD

<p align="center">
<kbd><img src="diagrams/assistant-invocationsettings.png" style="width: 220pt;"></kbd>
</p>


#### Thread Creation Settings

TBD

<p align="center">
<kbd><img src="diagrams/assistant-threadcreationsettings.png" style="width: 132pt;"></kbd>
</p>

### Agent Implementation

TBD

<p align="center">
<kbd><img src="diagrams/assistant-agent.png"  style="width: 720pt;"></kbd>
</p>

TBD

|Method Name|Description|
---|---
Create|TBD
ListDefinitions|TBD
Retrieve|TBD
CreateThread|TBD
DeleteThread|TBD
AddChatMessage|TBD
GetThreadMessages|TBD
Delete|TBD
Invoke|TBD
GetChannelKeys|TBD
CreateChannel|TBD


### Vector Store Support

TBD

<p align="center">
<kbd><img src="diagrams/assistant-vectorstore.png"  style="width: 720pt;"></kbd>
</p>


### Class Inventory
TBD

|Class Name|Description|
---|---
OpenAIAssistantAgent|TBD
OpenAIAssistantChannel|TBD
OpenAIAssistantDefinition|TBD
OpenAIAssistantExecutionSettings|TBD
OpenAIAssistantInvocationSettings|TBD
OpenAIServiceConfiguration|TBD
OpenAIVectorStore|TBD
OpenAIVectorStoreBuilder|TBD