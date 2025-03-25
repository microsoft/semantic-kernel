// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.OpenAIResponses;

/// <summary>
/// This example demonstrates how to manage conversation state during a model interaction using <see cref="OpenAIResponsesAgent"/>.
/// OpenAI provides a few ways to manage conversation state, which is important for preserving information across multiple messages or turns in a conversation.
/// </summary>
public class Step02_ConversationState(ITestOutputHelper output) : BaseResponsesAgentTest(output)
{
    [Fact]
    public async Task ManuallyConstructPastConversationAsync()
    {
        // Define the agent
        OpenAIResponsesAgent agent = new(this.Client)
        {
            StoreEnabled = false,
        };

        ICollection<ChatMessageContent> messages =
            [
            new ChatMessageContent(AuthorRole.User, "knock knock."),
            new ChatMessageContent(AuthorRole.Assistant, "Who's there?"),
            new ChatMessageContent(AuthorRole.User, "Orange.")
            ];

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync(messages);
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task ManuallyManageConversationStateWithResponsesApiAsync()
    {
        // Define the agent
        OpenAIResponsesAgent agent = new(this.Client)
        {
            StoreEnabled = false,
        };

        string[] messages =
            [
            "Tell me a joke?",
            "Tell me another?",
            ];

        // Invoke the agent and output the response
        AgentThread? agentThread = null;
        foreach (string message in messages)
        {
            var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, message), agentThread);
            await foreach (AgentResponseItem<ChatMessageContent> responseItem in responseItems)
            {
                agentThread = responseItem.Thread;
                WriteAgentChatMessage(responseItem.Message);
            }
        }
    }

    [Fact]
    public async Task ManuallyManageConversationStateWithChatCompletionsApiAsync()
    {
        // Define the agent
        OpenAIResponsesAgent agent = new(this.Client)
        {
            StoreEnabled = true,
        };

        string[] messages =
            [
            "Tell me a joke?",
            "Explain why this is funny.",
            ];

        // Invoke the agent and output the response
        AgentThread? agentThread = null;
        foreach (string message in messages)
        {
            var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, message), agentThread);
            await foreach (AgentResponseItem<ChatMessageContent> responseItem in responseItems)
            {
                agentThread = responseItem.Thread;
                WriteAgentChatMessage(responseItem.Message);
            }
        }
    }
}
