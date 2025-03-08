
# Agent Framework - Assistant V2 Migration

## Context and Problem Statement

Open AI has release the _Assistants V2_ API.  This builds on top of the V1 _assistant_ concept, but also invalidates certain V1 features.  In addition, the _dotnet_ API that supports _Assistant V2_ features is entirely divergent on the `Azure.AI.OpenAI.Assistants` SDK that is currently in use.

### Open Issues
- **Streaming:** To be addressed as a discrete feature


## Design

Migrating to Assistant V2 API is a breaking change to the existing package due to:
- Underlying capability differences (e.g. `file-search` vs `retrieval`)
- Underlying V2 SDK is version incompatible with V1 (`OpenAI` and `Azure.AI.OpenAI`)

### Agent Implementation

The `OpenAIAssistant` agent is roughly equivalent to its V1 form save for:

- Supports options for _assistant_, _thread_, and _run_
- Agent definition shifts to `Definition` property
- Convenience methods for producing an OpenAI client

Previously, the agent definition as exposed via direct properties such as:

- `FileIds`
- `Metadata`

This has all been shifted and expanded upon via the `Definition` property which is of the same type (`OpenAIAssistantDefinition`) utilized to create and query an assistant.

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


### Class Inventory
This section provides an overview / inventory of all the public surface area described in this ADR.

|Class Name|Description|
---|---
**OpenAIAssistantAgent**|An `Agent` based on the Open AI Assistant API
**OpenAIAssistantChannel**|An 'AgentChannel' for `OpenAIAssistantAgent` (associated with a _thread-id_.)
**OpenAIAssistantDefinition**|All of the metadata / definition for an Open AI Assistant.  Unable to use the _Open AI API_ model due to implementation constraints (constructor not public).
**OpenAIAssistantExecutionOptions**|Options that affect the _run_, but defined globally for the agent/assistant.
**OpenAIAssistantInvocationOptions**|Options bound to a discrete run, used for direct (no chat) invocation.
**OpenAIThreadCreationOptions**|Options for creating a thread that take precedence over assistant definition, when specified.
**OpenAIServiceConfiguration**|Describes the service connection and used to create the `OpenAIClient`


### Run Processing

The heart of supporting an _assistant_ agent is creating and processing a `Run`.

A `Run` is effectively a discrete _assistant_ interaction on a `Thread` (or conversation).

- https://platform.openai.com/docs/api-reference/runs
- https://platform.openai.com/docs/api-reference/run-steps

This `Run` processing is implemented as internal logic within the _OpenAI Agent Framework_ that is outlined here:

Initiate processing using: 

- `agent` -> `OpenAIAssistantAgent`
- `client` -> `AssistantClient`
- `threadid` -> `string`
- `options` -> `OpenAIAssistantInvocationOptions` (optional)


Perform processing:

- Verify `agent` not deleted
- Define `RunCreationOptions`
- Create the `run` (based on `threadid` and `agent.Id`)
- Process the run:

    do

    - Poll `run` status until is not _queued_, _in-progress_, or _cancelling_
    - Throw if `run` status is _expired_, _failed_, or _cancelled_
    - Query `steps` for `run`

    - if `run` status is _requires-action_
        
        - process function `steps`

        - post function results

    - foreach (`step` is completed)

        - if (`step` is tool-call) generate and yield tool content

        - else if (`step` is message) generate and yield message content

    while (`run` status is not completed)


### Vector Store Support

_Vector Store_ support is required in order to enable usage of the `file-search` tool.  

In alignment with V2 streaming of the `FileClient`, the caller may also directly target `VectorStoreClient` from the _OpenAI SDK_.


### Definition / Options Classes

Specific configuration/options classes are introduced to support the ability to define assistant behavior at each of the supported articulation points (i.e. _assistant_, _thread_, & _run_).

|Class|Purpose|
|---|---|
|`OpenAIAssistantDefinition`|Definition of the assistant.  Used when creating a new assistant, inspecting an assistant-agent instance, or querying assistant definitions.|
|`OpenAIAssistantExecutionOptions`|Options that affect run execution, defined within assistant scope.|
|`OpenAIAssistantInvocationOptions`|Run level options that take precedence over assistant definition, when specified.|
|`OpenAIAssistantToolCallBehavior`|Informs tool-call behavior for the associated scope: assistant or run.|
|`OpenAIThreadCreationOptions`|Thread scoped options that take precedence over assistant definition, when specified.|
|`OpenAIServiceConfiguration`|Informs the which service to target, and how.|


#### Assistant Definition

The `OpenAIAssistantDefinition` was previously used only when enumerating a list of stored agents.  It has been evolved to also be used as input for creating and agent and exposed as a discrete property on the `OpenAIAssistantAgent` instance.

This includes optional `ExecutionOptions` which define default _run_ behavior.  Since these execution options are not part of the remote assistant definition, they are persisted in the assistant metadata for when an existing agent is retrieved.  `OpenAIAssistantToolCallBehavior` is included as part of the _execution options_ and modeled in alignment with the `ToolCallBehavior` associated with _AI Connectors_.

> Note: Manual function calling isn't currently supported for `OpenAIAssistantAgent` or `AgentChat`  and is planned to be addressed as an enhancement.  When this supported is introduced, `OpenAIAssistantToolCallBehavior` will determine the function calling behavior (also in alignment with the `ToolCallBehavior` associated with _AI Connectors_).

**Alternative (Future?)**

A pending change has been authored that introduces `FunctionChoiceBehavior` as a property of the base / abstract `PromptExecutionSettings`.  Once realized, it may make sense to evaluate integrating this pattern for `OpenAIAssistantAgent`.  This may also imply in inheritance relationship of `PromptExecutionSettings` for both `OpenAIAssistantExecutionOptions` and `OpenAIAssistantInvocationOptions` (next section).

**DECISION**: Do not support `tool_choice` until the `FunctionChoiceBehavior` is realized.

<p align="center">
<kbd><img src="diagrams/assistant-definition.png"  style="width: 500pt;"></kbd>
</p>


#### Assistant Invocation Options

When invoking an `OpenAIAssistantAgent` directly (no-chat), definition that only apply to a discrete run may be specified.  These definition are defined as `OpenAIAssistantInvocationOptions` and overtake precedence over any corresponding assistant or thread definition.

> Note: These definition are also impacted by the `ToolCallBehavior` / `FunctionChoiceBehavior` quandary.

<p align="center">
<kbd><img src="diagrams/assistant-invocationsettings.png" style="width: 370pt;"></kbd>
</p>


#### Thread Creation Options

When invoking an `OpenAIAssistantAgent` directly (no-chat), a thread must be explicitly managed.  When doing so, thread specific options may be specified.  These options are defined as `OpenAIThreadCreationOptions` and take precedence over any corresponding assistant definition.

<p align="center">
<kbd><img src="diagrams/assistant-threadcreationsettings.png" style="width: 132pt;"></kbd>
</p>


#### Service Configuration

The `OpenAIServiceConfiguration` defines how to connect to a specific remote service, whether it be OpenAI, Azure, or proxy.  This eliminates the need to define multiple overloads for each call site that results in a connection to the remote API service (i.e. create a _client)_.

> Note: This was previously named `OpenAIAssistantConfiguration`, but is not necessarily assistant specific.

<p align="center">
<kbd><img src="diagrams/assistant-serviceconfig.png"  style="width: 520pt;"></kbd>
</p>

