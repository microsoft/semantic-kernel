// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.OpenAIResponseAgents;

/// <summary>
/// This example demonstrates how to manage conversation state during a model interaction using <see cref="OpenAIResponseAgent"/>.
/// OpenAI provides a few ways to manage conversation state, which is important for preserving information across multiple messages or turns in a conversation.
/// See: https://platform.openai.com/docs/guides/conversation-state?api-mode=responses for more information.
/// </summary>
public class Step02_OpenAIResponseAgent_ConversationState(ITestOutputHelper output) : BaseResponsesAgentTest(output)
{
    [Fact]
    public async Task ManuallyConstructPastConversationAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            StoreEnabled = false,
        };

        ICollection<ChatMessageContent> messages =
        [
            new ChatMessageContent(AuthorRole.User, "knock knock."),
            new ChatMessageContent(AuthorRole.Assistant, "Who's there?"),
            new ChatMessageContent(AuthorRole.User, "Orange.")
        ];
        foreach (ChatMessageContent message in messages)
        {
            WriteAgentChatMessage(message);
        }

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync(messages);
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task ManuallyConstructPastConversationStreamingAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            StoreEnabled = false,
        };

        ICollection<ChatMessageContent> messages =
        [
            new ChatMessageContent(AuthorRole.User, "knock knock."),
            new ChatMessageContent(AuthorRole.Assistant, "Who's there?"),
            new ChatMessageContent(AuthorRole.User, "Orange.")
        ];
        foreach (ChatMessageContent message in messages)
        {
            WriteAgentChatMessage(message);
        }

        // Invoke the agent and output the response
        var responseItems = agent.InvokeStreamingAsync(messages);
        Console.Write("\n# assistant: ");
        await foreach (StreamingChatMessageContent responseItem in responseItems)
        {
            Console.Write(responseItem.Content);
        }
    }

    [Fact]
    public async Task ManageConversationStateWithResponseIdAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            StoreEnabled = false,
        };

        string[] messages =
        [
            "Tell me a joke?",
            "Explain why this is funny?",
        ];

        // Invoke the agent and output the response
        AgentThread? agentThread = null;
        foreach (string message in messages)
        {
            var userMessage = new ChatMessageContent(AuthorRole.User, message);
            WriteAgentChatMessage(userMessage);

            var responseItems = agent.InvokeAsync(userMessage, agentThread);
            await foreach (AgentResponseItem<ChatMessageContent> responseItem in responseItems)
            {
                agentThread = responseItem.Thread;
                WriteAgentChatMessage(responseItem.Message);
            }
        }
    }

    [Fact]
    public async Task ManageConversationStateWithResponseIdStreamingAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            StoreEnabled = false,
        };

        string[] messages =
        [
            "Tell me a joke?",
            "Explain why this is funny?",
        ];

        // Invoke the agent and output the response
        AgentThread? agentThread = null;
        foreach (string message in messages)
        {
            var userMessage = new ChatMessageContent(AuthorRole.User, message);
            WriteAgentChatMessage(userMessage);

            Console.Write("\n# assistant: ");
            var responseItems = agent.InvokeStreamingAsync(userMessage, agentThread);
            await foreach (AgentResponseItem<StreamingChatMessageContent> responseItem in responseItems)
            {
                agentThread = responseItem.Thread;
                Console.Write(responseItem.Message.Content);
            }
        }
    }

    [Fact]
    public async Task StoreConversationStateAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
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
            var userMessage = new ChatMessageContent(AuthorRole.User, message);
            WriteAgentChatMessage(userMessage);

            var responseItems = agent.InvokeAsync(userMessage, agentThread);
            await foreach (AgentResponseItem<ChatMessageContent> responseItem in responseItems)
            {
                agentThread = responseItem.Thread;
                WriteAgentChatMessage(responseItem.Message);
            }
        }

        // Display the contents in the latest thread
        if (agentThread is not null)
        {
            this.Output.WriteLine("\n\nResponse Thread Messages\n");
            var responseAgentThread = agentThread as OpenAIResponseAgentThread;
            var threadMessages = responseAgentThread?.GetMessagesAsync();
            if (threadMessages is not null)
            {
                await foreach (var threadMessage in threadMessages)
                {
                    WriteAgentChatMessage(threadMessage);
                }
            }

            await agentThread.DeleteAsync();
        }
    }

    [Fact]
    public async Task StoreConversationStateWithStreamingAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
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
            var userMessage = new ChatMessageContent(AuthorRole.User, message);
            WriteAgentChatMessage(userMessage);

            Console.Write("\n# assistant: ");
            var responseItems = agent.InvokeStreamingAsync(userMessage, agentThread);
            await foreach (AgentResponseItem<StreamingChatMessageContent> responseItem in responseItems)
            {
                agentThread = responseItem.Thread;
                Console.Write(responseItem.Message.Content);
            }
        }

        // Display the contents in the latest thread
        if (agentThread is not null)
        {
            this.Output.WriteLine("\n\nResponse Thread Messages\n");
            var responseAgentThread = agentThread as OpenAIResponseAgentThread;
            var threadMessages = responseAgentThread?.GetMessagesAsync();
            if (threadMessages is not null)
            {
                await foreach (var threadMessage in threadMessages)
                {
                    WriteAgentChatMessage(threadMessage);
                }
            }

            await agentThread.DeleteAsync();
        }
    }
}
