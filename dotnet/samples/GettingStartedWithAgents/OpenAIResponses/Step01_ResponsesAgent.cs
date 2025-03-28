// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.OpenAIResponsesAgents;

/// <summary>
/// This example demonstrates using <see cref="OpenAIResponsesAgent"/>.
/// </summary>
public class Step01_ResponsesAgent(ITestOutputHelper output) : BaseResponsesAgentTest(output)
{
    [Fact]
    public async Task UseOpenAIResponseAgentAsync()
    {
        // Define the agent
        OpenAIResponsesAgent agent = new(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in English and French.",
        };

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "What is the capital of France?"));
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task UseOpenAIResponseAgentWithMessagesAsync()
    {
        // Define the agent
        OpenAIResponsesAgent agent = new(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in English and French."
        };

        ICollection<ChatMessageContent> messages =
        [
            new ChatMessageContent(AuthorRole.User, "What is the capital of France?"),
            new ChatMessageContent(AuthorRole.User, "What is the capital of Ireland?")
        ];

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync(messages);
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task UseOpenAIResponseAgentWithThreadedConversationAsync()
    {
        // Define the agent
        OpenAIResponsesAgent agent = new(this.Client)
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
            var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, message), agentThread);
            await foreach (AgentResponseItem<ChatMessageContent> responseItem in responseItems)
            {
                // Update the thread so the previous response id is used
                agentThread = responseItem.Thread;

                WriteAgentChatMessage(responseItem.Message);
            }
        }
    }
}
