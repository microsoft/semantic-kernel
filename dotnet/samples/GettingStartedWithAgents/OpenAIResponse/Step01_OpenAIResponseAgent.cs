// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.OpenAIResponseAgents;

/// <summary>
/// This example demonstrates using <see cref="OpenAIResponseAgent"/>.
/// </summary>
public class Step01_OpenAIResponseAgent(ITestOutputHelper output) : BaseResponsesAgentTest(output)
{
    [Fact]
    public async Task UseOpenAIResponseAgentAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in English and French.",
        };

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync("What is the capital of France?");
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task UseOpenAIResponseAgentStreamingAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in English and French.",
        };

        // Invoke the agent and output the response
        var responseItems = agent.InvokeStreamingAsync("What is the capital of France?");
        await WriteAgentStreamMessageAsync(responseItems);
    }

    [Fact]
    public async Task UseOpenAIResponseAgentWithThreadedConversationAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in the users preferred language.",
        };

        string[] messages =
        [
            "My name is Bob and my preferred language is French.",
            "What is the capital of France?",
            "What is the capital of Spain?",
            "What is the capital of Italy?"
        ];

        // Initial thread can be null as it will be automatically created
        AgentThread? agentThread = null;

        // Invoke the agent and output the response
        foreach (string message in messages)
        {
            Console.Write($"Agent Thread Id: {agentThread?.Id}");
            var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, message), agentThread);
            await foreach (AgentResponseItem<ChatMessageContent> responseItem in responseItems)
            {
                // Update the thread so the previous response id is used
                agentThread = responseItem.Thread;

                WriteAgentChatMessage(responseItem.Message);
            }
        }
    }

    [Fact]
    public async Task UseOpenAIResponseAgentWithThreadedConversationStreamingAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in the users preferred language.",
        };

        string[] messages =
        [
            "My name is Bob and my preferred language is French.",
            "What is the capital of France?",
            "What is the capital of Spain?",
            "What is the capital of Italy?"
        ];

        // Initial thread can be null as it will be automatically created
        AgentThread? agentThread = null;

        // Invoke the agent and output the response
        foreach (string message in messages)
        {
            Console.Write($"Agent Thread Id: {agentThread?.Id}");
            var responseItems = agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, message), agentThread);

            // Update the thread so the previous response id is used
            agentThread = await WriteAgentStreamMessageAsync(responseItems);
        }
    }
}
