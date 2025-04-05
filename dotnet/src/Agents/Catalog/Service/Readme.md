# Overview

This project defines the patterns for building "Out of the Box" (OOTB) Agents with _Semantic Kernel_ as well 
as the contract for how an _OOTB Agent_ is initialize and invoked by the hosting service (Agent Host).

Since the _agent host_ needs a fixed contract to be able to create and invoke any _OOTB Agent_ without knowledge
of any specific implementation detail (such as the shape of the constructor), a _provider_ pattern is defined where
each specific _OOTB Agent_ has a dedicated provider.  A factory pattern is preset for creating the provider based
only on inspect the OOTB Agent type.

In addition two base-classes are defined for the purpose of building an OOTB Agent.  


# Contract

At a high-level, the contract between the _agent host_ and the _OOTB Agent_ is defined as:

## Input

- The .NET type of the agent being invoked
- Configuration settings
- Logging services
- The agent identifier
- The agent name
- The conversation thread identifier

## Output

- Agent Response - Non-Streaming
- Agent Response - Streaming
- Diagnostics: Logging, Trace, Metrics


# Details

## Agent Definition

An _OOTB Agent_ may be defined as a subclass of:

#### [`ServiceAgent`](./ServiceAgent.cs) 
  
This is a simple subclass of [`Agent`](../../Abstractions/Agent.cs) that removes any confusion around
the need to implement the abstract methods for the `AgentChannel`
(since its not expected for an _OOTB Agent_ to integrate to `AgentChat`, whose future is limited).
    
This class also serves as a placeholder for any common functionality that identified during this initial prototyping phase.

> Worse case, this class can be removed later if no common functionality is identified.



#### [`ComposedServiceAgent`](./ComposedServiceAgent.cs)

This is a subclass of [`ServiceAgent`](./ServiceAgent.cs) that relies on an inner [`Agent`](../../Abstractions/Agent.cs) to 
perform the actual work of the agent since (for example) [`ChatCompletionAgent`](../../Core/ChatCompletionAgent.cs) 
is `sealed` and cannot be extended.


## Agent Initialization

#### [`ServiceAgentProvider`](./ServiceAgentProvider.cs)

This provider defines the contract for how an _OOTB Agent_ ([`ServiceAgent`](./ServiceAgent.cs)) is initialized and 
invoked by the hosting service (or _agent host_).

- `constructor`: The constructor for any `ServiceAgentProvider` subclass is expected to only accept two parameters:

    - `IConfiguration` - Configuration related to the Foundry project and agent instance as well as any service specific configuration.
    
    - `ILoggerFactory` - Logging services to be used for the entire agent lifecycle.

    > The [`ServiceAgentProviderFactory`](./ServiceAgentProviderFactory.cs) requires this two parameter constructor to be present on any provider subsclass.

- `CreateAgentAsync(string id, string? name) -> Agent`:
    
    - Provides an instance of the _OOTB Agent_ to the _agent host_.

    - Isolates the _agent host_ from the details of how the _OOTB Agent_ is created.

    - `id` and `name` parameters are specific to the usage of the _OOTB Agent_ and provided by the _agent host_


- `AgentThread CreateThreadAsync(string threadId)  -> AgentThread`:
    
    - Invoking a _Semantic Kernel_ agent requires that an `AgentThread` be provided.  
      This method isolates the _agent host_ from the details on how to create and initialize this `AgentThread`.

    - `threadId` is specific to the specific invocation of the agent and identifies an external thread that
      defines the conversation for which the agent is being requested to respond.

#### [`ServiceAgentProviderFactory`](./ServiceAgentProviderFactory.cs)

This is the entry point for creating the `ServiceAgentProvider` for a specific _OOTB Agent_.

- `CreateServicesProvider(Type agentType, IConfiguration configuration, ILoggerFactory loggerFactory) -> ServiceAgentProvider`

#### [`ServiceAgentProviderAttribute`](./ServiceAgentProviderAttribute.cs)

Associates a `ServiceAgentProvider` with an `ServiceAgent`.  This attribute is consumed by the `ServiceAgentProviderFactory` to initialize a provider.

## Example

The following pattern shows how any _OOTB Agent_ can be created and invoked by the _agent host_ 
without any knowledge of the specific implementation details of the agent othen than the .NET type.

#### Implementation

```csharp
// Define the provider
public sealed class MyOOTBAgentProvider : ServiceAgentProvider { ... }

// Define the agent
[ServiceAgentProvider<MyOOTBAgentProvider>]
public sealed class MyOOTBAgent : ServiceAgent { ... }
```

#### Common pattern

```csharp
// Create the provider via the factory
ServiceAgentProvider provider = ServiceAgentProviderFactory.CreateServicesProvider(typeof(MyOOTBAgent), configuration, loggerFactory);

// Create the agent via the provider
Agent agent = await provider.CreateAgentAsync("my-agent-id", "my-agent-name");

// Create the agent-thread via the provider
AgentThread thread = await provider.CreateThreadAsync("my-thread-id");

// Invoke the agent and capture the response
IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> responses = await agent.InvokeAsync([], thread);
```
