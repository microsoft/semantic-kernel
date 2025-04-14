---
# These are optional elements. Feel free to remove any of them.
status: { proposed }
contact: { }
date: { 2025-04-11 }
deciders: { }
consulted: { }
informed: { }
---

# Multi-agent Orchestration

> Items marked with an asterisk (*) are not yet fully fleshed out and need further research.

## Context

The industry is moving up the stack to build more complex systems using LLMs. From interacting with foundation models to building RAG systems, and now creating AI agents to perform more complex tasks, the desire for a multi-agent framework is growing.

With the recent GA of the Semantic Kernel Agent Framework, we are now able to build on top of it to create a multi-agent orchestration framework. This will allow our customers to unlock even more complex scenarios and use cases.

In addition, with the collaboration with the AutoGen team and the shared runtime abstractions, we can leverage the work done in AutoGen to build a multi-agent orchestration framework more rapidly.

## Problem Statement

The current state of the Semantic Kernel Agent Framework is limited to single agents. We need to build a multi-agent orchestration framework to allow our customers to build more complex systems using multiple agents.

### AutoGen shared runtime abstractions

The AutoGen team has built a runtime that supports pub-sub communication between actors in a system. We have had the opportunity to leverage this work, which led to a shared runtime abstraction that our framework will depend on.
With the shared runtime abstraction, our framework will support local and distributed use cases.

## Considerations

### Out-of-the-box orchestrations

| **Orchestrations**       | **Description**                                                                                                                                                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Concurrent**     | - Consists of multiple actors that run in parallel. <br> - Tasks are broadcasted to all actors. <br> - The results are collected and returned to the caller when all actors finish. <br> - The order of the results is not guaranteed. |
| **Sequential**     | - Consists of multiple actors that run in sequence. <br> - The output of the previous actor is the input of the next actor. <br> - The result is collected and returned to the caller when the last actor finishes.                  |
| **Handoff**        | - Consists of multiple actors. <br> - The actors can decide the next actor to send the task to. <br> - The full context (conversation) of the previous actor is passed to the next actor. <br> - Human-in-the-loop may be supported. <br> - The result is collected and returned to the caller when the orchestration finishes. |
| **GroupChat**      | - Consists of multiple actors. <br> - A group manager actor is responsible for managing the state of the group chat. <br> - **Key Features:** <br> &nbsp;&nbsp;&nbsp;&nbsp;- User input: Requests input from the user. <br> &nbsp;&nbsp;&nbsp;&nbsp;- Termination: Ends when a termination condition is met, and results are returned. <br> &nbsp;&nbsp;&nbsp;&nbsp;- Next actor: Decides the next actor to invoke. <br> - Human-in-the-loop must be supported. <br> - The result is collected and returned to the caller when the orchestration finishes. |
| **Magentic One**   | - Group chat-like orchestration with unique features. <br> - Inspired by [Magentic One](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/).                  |

### Support the ability to create custom multi-agent orchestrations

Our framework should support customers to create more advanced orchestrations for their specific use cases using the same building blocks we use to build the out-of-the-box orchestrations.

#### Building blocks

| **Component**         | **Details**                                                                                                                                                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Agent actor**       | - Semantic Kernel agent <br> - Agent thread <br> - Support for streaming?                                                                                                                                                       |
| **Orchestration actor** | - Broadcast messages to an external topic (e.g., the result of the orchestration) <br> - Send directly to an actor external to the orchestration (e.g., the result of the orchestration) <br> - Receive messages from an external topic (e.g., the start of the orchestration) <br> - Receive messages from an actor external to the orchestration (e.g., the start of the orchestration) |
| **Orchestration**     | - Consists of one orchestration actor and multiple agent actors and other orchestrations. <br> - Support for streaming?                                                                                                         |
| **Data transform logic** | - Provide hooks to transform the input and output of the orchestration to **custom types** and for nesting orchestrations.                                                                                                     |

An orchestration can have multiple agent actors and child orchestrations, but only one orchestration actor.

```mermaid
graph TD
  %% External
  EXT_Topic[External Topic]
  EXT_Actor[External Actor]

  %% Outer Block
  subgraph Orchestration
    subgraph OA[Orchestration Actor]
      InputTransform[Input Transform]
      OutputTransform[Output Transform]
    end

    subgraph Members[Members]
      AG0[agent 0]
      AG1[agent 1]
      SO0[sub orchestration 0]
      SO1[sub orchestration 1]
      IT[Internal Topic]
    end

  end

  %% Connections
  EXT_Topic <--> |Broadcast| OA
  EXT_Actor <--> |Direct messaging| OA
  OA <--> |Broadcast| IT

  OA <-.Direct messaging.-> AG0
  OA <-.Direct messaging.-> AG1
  OA <-.Direct messaging.-> SO0
  OA <-.Direct messaging.-> SO1
```

#### Runtime

- Orchestration should only depend upon the runtime abstraction
- The runtime is provided when the orchestration is invoked, not when the orchestration is created.
- The runtime lifecycle is managed by the application (external to the orchestration).
- Multiple orchestrations can share the same runtime instance (orchestration boundaries).
  - How do we make sure there is no name (agents and subscriptions) collisions.

### Graph-like structure with lazy evaluation

- An orchestration is simply a definition of a directed graph of actors and orchestrations.
- Actors and child orchestrations are registered in the runtime before execution starts.
- The runtime is responsible for executing the graph and managing the lifecycle of the actors and orchestrations.

### Support nested orchestrations

Example:

```mermaid
graph TD
  subgraph Concurrent
    OA0[Orchestration Actor]
    OA1[Orchestration Actor]
    subgraph Sequential_0
        AgentA_0
        AgentB_0
        AgentA_0 --> AgentB_0
    end

    subgraph Sequential_1
        AgentA_1
        AgentB_1
        AgentA_1 --> AgentB_1
    end

    OA0 --> Sequential_0
    OA0 --> Sequential_1
    Sequential_0 --> RCA[Result Collection Actor]
    Sequential_1 --> RCA[Result Collection Actor]
    RCA --> OA1
  end

  External0[External] --> OA0
  OA1 --> External1[External]
```

> The two orchestration actors in the diagram are the same actor. The two external actors are the same actor. Separating them is just for a cleaner diagram.

The above is a simple example that shows what a nested multi-agent orchestration looks like. This orchestration contains two sequential orchestrations that run in parallel.
The actors are registered with the runtime whose lifetime is managed by the runtime, not the application.

### Orchestration invocation paradigms

- Direct invocation: the orchestration is invoked directly by the user.
- Indirect invocation: the orchestration actor receives a message from another actor within a parent orchestration.
- State management
  - Orchestrations are stateless.
  - Use memory in Semantic Kernel agents to store extracted user context for future invocations.

### Human in the loop

- Keep the user in the loop and allow them to intervene in the orchestration process
- How would this work for a RestAPI/distributed system?
- How would this work for an orchestration or an agent that is nested inside another orchestration?
  - Does the signal need to bubble up to the root orchestration?
  - Other possibilities?

### Distribution

- Can nested orchestrations be distributed?
- Can agents factories be distributed?
- If registration occurs per invocation, how to register remote orchestrations/agents?

### Save states of the agents in an orchestration and rehydration

- Being able to save the state of the orchestration process while waiting for user input and restore it later when user provides input for scalability
- Recursively save the state of all agents and child orchestrations, including threads, chat history, and context from the root orchestration

### Support declarative orchestrations*

### Guardrails*

- In the orchestration level?
- In the agent level?
