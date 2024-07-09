
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

The following table describes the purpose of diagramed methods on the `OpenAIAssistantAgent`.

|Method Name|Description|
---|---
**Create**|Create a new assistant agent
**ListDefinitions**|List existing assistant definitions
**Retrieve**|Retrieve an existing assistant
**CreateThread**|Create an assistant thread
**DeleteThread**|Delete an assistant thread
**AddChatMessage**|Add a message to an assistant thread
**GetThreadMessages**|Retrieve all messages from an assistant thread
**Delete**|Delete the assistant agent's definition (puts agent into a terminal state)
**Invoke**|Invoke the assistant agent (no chat)
**GetChannelKeys**|Inherited from `Agent`
**CreateChannel**|Inherited from `Agent`


### Vector Store Support

_Vector Store_ support is provided in order to enable usage of the `file-search` tool.  While the _playground_ and API support implicit creation of a vector-store when providing only a list of file identifiers, the _Agent Framework_ encourages creation of vector-store separate from the agent lifecycle.

<p align="center">
<kbd><img src="diagrams/assistant-vectorstore.png"  style="width: 720pt;"></kbd>
</p>


### Class Inventory
This section provides an overview / inventory of all the public surface area described in this ADR.

|Class Name|Description|
---|---
**OpenAIAssistantAgent**|An `Agent` based on the Open AI Assistant API
**OpenAIAssistantChannel**|An 'AgentChannel' for `OpenAIAssistantAgent` (associated with a _thread-id_.)
**OpenAIAssistantDefinition**|All of the metadata / definition for an Open AI Assistant.  Unable to use the _Open AI API_ model due to implementation constraints (constructor not public).
**OpenAIAssistantExecutionSettings**|Setting that affect the _run_, but defined globally for the agent/assistant.
**OpenAIAssistantInvocationSettings**|Settings bound to a discrete run, used for direct (no chat) invocation.
**OpenAIServiceConfiguration**|Describes the service connection and used to create the `OpenAIClient`
**OpenAIVectorStore**|Used to query and manipulate a vector-store.  Also supports listing available vector-stores (static).
**OpenAIVectorStoreBuilder**|Supports creation of an vector-store.