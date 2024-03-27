---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: SergeyMenshykh
date: 2024-01-24
deciders: markwallace-microsoft, matthewbolanos
consulted: rogerbarreto, dmytrostruk
informed:
---

# SK Agents Overview and High Level Design

## Context and Problem Statement
Currently, agents in SK .NET are represented by the [IAgent](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Experimental/Agents/IAgent.cs) interface, the [Agent](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Experimental/Agents/Internal/Agent.cs) class, and a set of classes in the [Agents folder](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Experimental/Agents). These classes enable agent communication with the OpenAI Assistant API, agent collaboration, and more.  
   
The [Agent](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Experimental/Agents/Internal/Agent.cs) class is the only implementation of an agent in SK that utilizes the [OpenAI Assistant API](https://platform.openai.com/docs/assistants/how-it-works). It accomplishes this through a series of abstractions, which are implemented as wrappers around the OpenAI Assistant API, hiding the complexity and details of HTTP calls to the OpenAI API. 
   
The [IAgent](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Experimental/Agents/IAgent.cs) interface is implemented by the Agent class. This interface is intended to be implemented by all the future agents. Its design was shaped around the OpenAI Assistant API and contains several members that might not be relevant to all agents, such as NewThreadAsync, AddFileAsync, FileIds, etc. This can make it more challenging to use the interface when building custom agents.

Current agent functionality lacks the necessary building blocks and a unified agent interface, which would enable quick and easy configuration of how agents collaborate. For example, it would be beneficial to create several agents, add them to an agent chat, and ask them to collaborate on solving a task at hand without writing any code to facilitate the collaboration. In cases where turn-based communication between two or more agents is required, it should be a matter of simply adding the agents to the agent turn-based chat to enable their collaboration.

## Decision Drivers
- SK should provide sufficient abstraction to enable the construction of agents that could utilize potentially any LLM API.
- SK should provide sufficient abstraction and building blocks for the most frequent types of agent collaboration. It should be easy to add new blocks as new collaboration methods emerge.
- SK should provide building blocks to modify agents' input and output to cover various customization scenarios.
- SK agents' input and output should be represented by the same data type, making it easy to pass the output of one agent as input to another.
- SK agents should leverage all SK tools DI, plugins, function-calling, etc.
- SK agents API should be as simple as possible so that other libraries can build their agents on top of it if needed.

## Agents Overview
Fundamentally an agent possesses the following characteristics:
- Identity: Allows each agent to be uniquely identified.
- Behavior: The manner in which an agent participates in a conversation
- Interaction: That an agent behavior is in response to other agents or input.

Various agents specializations might include:
- System Instructions: A set of directives that guide the agent's behavior.
- Tools/Functions: Enables the agent to perform specific tasks or actions.
- Settings: Agent specific settings.  For a chat-completion agents this might include LLM settings - such as Temperature, TopP, StopSequence, etc

## OpenAI Assistant API

<img src="./diagrams/open-ai-assistant-api-objects.png" alt="OpenAI Assistant API Objects.png" width="700"/>

[Source](https://platform.openai.com/docs/assistants/how-it-works/objects)

[Playground](https://platform.openai.com/playground)

## Unified Interface And Data Contract
To enable collaboration and customization scenarios, further details of which will be provided below, agents should have a unified interface. They should inherit from the same abstract Agent class and have one data type - AgentMessage, for both input and output data contracts. This will enable a very powerful and extensible model, allowing the addition of any agent to any chat/collaboration, regardless of its implementation, and enabling a seamless chat conversation where the agent's output message is added to the chat without any conversion, and the chat is sent as input for the next agent without any conversion as well.


Pros:  
- No changes are needed for existing agent chat/collaboration classes to accommodate new agents.  
- No custom logic is required in the chat/collaboration classes to support new agents.
   
Cons:  
- Some features of certain agents might not be fully utilized, as chat/collaboration classes are only aware of the unified interface supported by all agents.


## Agent Customization & Filters

To cover complex agent collaboration scenarios, it might be necessary to modify agents' input and/or output messages as they travel to and from Agents. This may be useful for various scenarios, such as converting agents' message content from one format/type to another. There could be situations when messages should not be propagated to Agents or not added to the collaboration chat. For example, in the scenario above where the PM, designer, and engineer collaborate on a new experience for the TODO app, the PM's behavior could be extended to generate a chat exit signal based on whether the function used by the agent indicates that the new 'Add item' user experience is good enough as POC:

```C#
class AgentCollaborationChat(Agent admin, Agent[] participants)
{
    async Task<AgentMessage[]> StartConversationAsync(AgentMessage[] messages)
    {
        ...
        while (chatExitCondition)
        {
            ...
            var result = await nextAgent.InvokeAsync(chat);
            ...
            chatExitCondition == string.Contains(result.Content, "exit_chat") // The chat can be parameterized with agent condition or callback.
        }
        ...
    }
}

Agent projectManager = new ChatCompletionAgent(name: "Mike", instructions: "You're a PM working on the new TODO app ....", ...);
projectManager.Plugins.AddFromType<UIUsabilityAssessor>()
projectManager = projectManager.PostProcess((reply) => {
    if(reply.IsFunctionCall)
    {
        if(reply.FunctionName == "EvaluateUsability")
        {
            if(reply.FunctionResult.IsCoreFunctionalityAccessible)
            {
                return new [] { new AgentMessage(role: "system", content: "exit_chat") };
            }

            return new [] { new AgentMessage(role: "system", content: "Peter/designer please improve the design so that core functionality is accessible.") };
        }
    }
    return reply;
});

Agent designer = new ChatCompletionAgent(name: "Peter", instructions: "You're a UI/UX designer ....", ...);

Agent engineer = new OpenAIAssistant(name: "Roy", instructions: "You are an engineer with front-end skills ...");

AgentCollaborationChat chat = new(admin: projectManager, participants: new {designer, engineer});

var result = await chat.StartConversationAsync(new[] { new AgentMessage(role: "user", content: "collaborate on a new user experience for the 'Add item' feature.") });
```
Some scenarios can be implemented without filters by just plugins. However, this may require extra hops to LLMs and prompt tuning to have those scenarios working.

Filter examples:
- PostProcess: Accepts an agent and a delegate capable of modifying or replacing messages returned by the agent. It calls the agent and then calls the delegate with the agent's response messages. Finally, it returns the modified messages to the caller.
- PreProcess: Accepts an agent and a delegate capable of modifying or replacing messages to be passed to the agent. It calls the callback to handle the messages and pass the modified messages to the agent. Returns the agent result to the caller.

Each of the filter can be implemented as a decorator pattern that will allow to build agents pipelines/chains: 
```C#
var agent = new ChatCompletionAgent(...)
    .PostProcess((m) => { Console.WriteLine($"Agent response: {m.Content}"); return m; })
    .PreProcess(m => { Console.WriteLine($"User input: {m.Content}"); return m; });

await agent.InvokeAsync(...);

```

SK, today, already has the concept of filters for [prompts](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/Filters/Prompt/IPromptFilter.cs) and [functions](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/Filters/Function/IFunctionFilter.cs). Ideally, the same approach should be taken for Agent filters.

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

