---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: westey-m
date: 2025-04-17
deciders: westey-m, markwallace-microsoft, alliscode, TaoChenOSU, moonbox3, crickman
consulted: westey-m, markwallace-microsoft, alliscode, TaoChenOSU, moonbox3, crickman
informed: westey-m, markwallace-microsoft, alliscode, TaoChenOSU, moonbox3, crickman
---

# Agents with Memory

## What do we mean by Memory?

By memory we mean the capability to remember information and skills that are learned during
a conversation and re-use those later in the same conversation or later in a subsequent conversation.

## Context and Problem Statement

Today we support multiple agent types with different characteristics:

1. In process vs remote.
2. Remote agents that store and maintain conversation state in the service vs those that require the caller to provide conversation state on each invocation.

We need to support advanced memory capabilities across this range of agent types.

### Memory Scope

Another aspect of memory that is important to consider is the scope of different memory types.
Most agent implementations have instructions and skills but the agent is not tied to a single conversation.
On each invocation of the agent, the agent is told which conversation to participate in, during that invocation.

Memories about a user or about a conversation with a user is therefore extracted from one of these conversation and recalled
during the same or another conversation with the same user.
These memories will typically contain information that the user would not like to share with other users of the system.

Other types of memories also exist which are not tied to a specific user or conversation.
E.g. an Agent may learn how to do something and be able to do that in many conversations with different users.
With these type of memories there is of cousrse risk in leaking personal information between different users which is important to guard against.

### Packaging memory capabilities

All of the above memory types can be supported for any agent by attaching software components to conversation threads.
This is achieved via a simple mechanism of:

1. Inspecting and using messages as they are passed to and from the agent.
2. Passing additional context to the agent per invocation.

With our current `AgentThread` implementation, when an agent is invoked, all input and output messages are already passed to the `AgentThread`
and can be made available to any components attached to the `AgentThread`.
Where agents are remote/external and manage conversation state in the service, passing the messages to the `AgentThread` may not have any
affect on the thread in the service. This is OK, since the service will have already updated the thread during the remote invocation.
It does however, still allow us to subscribe to messages in any attached components.

For the second requirement of getting additional context per invocation, the agent may ask the thread passed to it, to in turn ask
each of the components attached to it, to provide context to pass to the Agent.
This enables the component to provide memories that it contains to the Agent as needed.

Different memory capabilities can be built using separate components. Each component would have the following characteristics:

1. May store some context that can be provided to the agent per invocation.
2. May inspect messages from the conversation to learn from the conversation and build its context.
3. May register plugins to allow the agent to directly store, retrieve, update or clear memories.

### Suspend / Resume

Building a service to host an agent comes with challenges.
It's hard to build a stateful service, but service consumers expect an experience that looks stateful from the outside.
E.g. on each invocation, the user expects that the service can continue a conversation they are having.

This means that where the the service is exposing a local agent with local conversation state management (e.g. via `ChatHistory`)
that conversation state needs to be loaded and persisted for each invocation of the service.

It also means that any memory components that may have some in-memory state will need to be loaded and persisted too.

For cases like this, the `OnSuspend` and `OnResume` methods allow notification of the components that they need to save or reload their state.
It is up to each of these components to decide how and where to save state to or load state from.

## Proposed interface for Memory Components

The types of events that Memory Components require are not unique to memory, and can be used to package up other capabilities too.
The suggestion is therefore to create a more generally named type that can be used for other scenarios as well and can even
be used for non-agent scenarios too.

This type should live in the `Microsoft.SemanticKernel.Abstractions` nuget, since these components can be used by systems other than just agents.

```csharp
namespace Microsoft.SemanticKernel;

public abstract class AIContextBehavior
{
    public virtual IReadOnlyCollection<AIFunction> AIFunctions => Array.Empty<AIFunction>();

    public virtual Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default);
    public virtual Task OnThreadDeleteAsync(string? threadId, CancellationToken cancellationToken = default);

    // OnThreadCheckpointAsync not included in initial release, maybe in future.
    public virtual Task OnThreadCheckpointAsync(string? threadId, CancellationToken cancellationToken = default);

    public virtual Task OnNewMessageAsync(string? threadId, ChatMessage newMessage, CancellationToken cancellationToken = default);
    public abstract Task<string> OnModelInvokeAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default);

    public virtual Task OnSuspendAsync(string? threadId, CancellationToken cancellationToken = default);
    public virtual Task OnResumeAsync(string? threadId, CancellationToken cancellationToken = default);
}
```

## Managing multiple components

To manage multiple components I propose that we have a `AIContextBehavior`.
This class allows registering components and delegating new message notifications, ai invocation calls, etc. to the contained components.

## Integrating with agents

I propose to add a `AIContextBehaviorManager` to the `AgentThread` class, allowing us to attach components to any `AgentThread`.

When an `Agent` is invoked, we will call `OnModelInvokeAsync` on each component via the `AIContextBehaviorManager` to get
a combined set of context to pass to the agent for this invocation. This will be internal to the `Agent` class and transparent to the user.

```csharp
var additionalInstructions = await currentAgentThread.OnModelInvokeAsync(messages, cancellationToken).ConfigureAwait(false);
```

## Usage examples

### Multiple threads using the same memory component

```csharp
// Create a vector store for storing memories.
var vectorStore = new InMemoryVectorStore();
// Create a memory store that is tired to a "Memories" collection in the vector store and stores memories under the "user/12345" namespace.
using var textMemoryStore = new VectorDataTextMemoryStore<string>(vectorStore, textEmbeddingService, "Memories", "user/12345", 1536);

// Create a memory component to will pull user facts from the conversation, store them in the vector store
// and pass them to the agent as additional instructions.
var userFacts = new UserFactsMemoryComponent(this.Fixture.Agent.Kernel, textMemoryStore);

// Create a thread and attach a Memory Component.
var agentThread1 = new ChatHistoryAgentThread();
agentThread1.ThreadExtensionsManager.Add(userFacts);
var asyncResults1 = agent.InvokeAsync("Hello, my name is Caoimhe.", agentThread1);

// Create a second thread and attach a Memory Component.
var agentThread2 = new ChatHistoryAgentThread();
agentThread2.ThreadExtensionsManager.Add(userFacts);
var asyncResults2 = agent.InvokeAsync("What is my name?.", agentThread2);
// Expected response contains Caoimhe.
```

### Using a RAG component

```csharp
// Create Vector Store and Rag Store/Component
var vectorStore = new InMemoryVectorStore();
using var ragStore = new TextRagStore<string>(vectorStore, textEmbeddingService, "Memories", 1536, "group/g2");
var ragComponent = new TextRagComponent(ragStore, new TextRagComponentOptions());

// Upsert docs into vector store.
await ragStore.UpsertDocumentsAsync(
[
    new TextRagDocument("The financial results of Contoso Corp for 2023 is as follows:\nIncome EUR 174 000 000\nExpenses EUR 152 000 000")
    {
        SourceName = "Contoso 2023 Financial Report",
        SourceReference = "https://www.consoso.com/reports/2023.pdf",
        Namespaces = ["group/g2"]
    }
]);
    
// Create a new agent thread and register the Rag component
var agentThread = new ChatHistoryAgentThread();
agentThread.ThreadExtensionsManager.RegisterThreadExtension(ragComponent);

// Inovke the agent.
var asyncResults1 = agent.InvokeAsync("What was the income of Contoso for 2023", agentThread);
// Expected response contains the 174M income from the document.
```

## Decisions to make

### Extension base class name

1. ConversationStateExtension

    1.1. Long

2. MemoryComponent

    2.1. Too specific

3. AIContextBehavior

Decided 3. AIContextBehavior.

### Location for abstractions

1. Microsoft.SemanticKernel.<baseclass>
2. Microsoft.SemanticKernel.Memory.<baseclass>
3. Microsoft.SemanticKernel.Memory.<baseclass> (in separate nuget)

Decided: 1. Microsoft.SemanticKernel.<baseclass>.

### Location for memory components

1. A nuget for each component
2. Microsoft.SemanticKernel.Core nuget
3. Microsoft.SemanticKernel.Memory nuget
4. Microsoft.SemanticKernel.ConversationStateExtensions nuget

Decided: 2. Microsoft.SemanticKernel.Core nuget