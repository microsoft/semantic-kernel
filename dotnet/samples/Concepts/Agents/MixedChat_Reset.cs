// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Agents;

/// <summary>
/// Demonstrate the use of <see cref="AgentChat.ResetAsync"/>.
/// </summary>
public class MixedChat_Reset(ITestOutputHelper output) : BaseTest(output)
{
    private const string AgentInstructions =
        """
        The user may either provide information or query on information previously provided.
        If the query does not correspond with information provided, inform the user that their query cannot be answered.
        """;

    [Fact]
    public async Task ResetChatAsync()
    {
        OpenAIFileService fileService = new(TestConfiguration.OpenAI.ApiKey);

        // Define the agents
        OpenAIAssistantAgent assistantAgent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config: new(this.ApiKey, this.Endpoint),
                new()
                {
                    Name = nameof(OpenAIAssistantAgent),
                    Instructions = AgentInstructions,
                    ModelId = this.Model,
                });

        ChatCompletionAgent chatAgent =
            new()
            {
                Name = nameof(ChatCompletionAgent),
                Instructions = AgentInstructions,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input
        try
        {
            await InvokeAgentAsync(assistantAgent, "What is my favorite color?");
            await InvokeAgentAsync(chatAgent);

            await InvokeAgentAsync(assistantAgent, "I like green.");
            await InvokeAgentAsync(chatAgent);

            await InvokeAgentAsync(assistantAgent, "What is my favorite color?");
            await InvokeAgentAsync(chatAgent);

            await chat.ResetAsync();

            await InvokeAgentAsync(assistantAgent, "What is my favorite color?");
            await InvokeAgentAsync(chatAgent);
        }
        finally
        {
            await chat.ResetAsync();
            await assistantAgent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(Agent agent, string? input = null)
        {
            if (!string.IsNullOrWhiteSpace(input))
            {
                chat.AddChatMessage(new(AuthorRole.User, input));
                Console.WriteLine($"\n# {AuthorRole.User}: '{input}'");
            }

            await foreach (ChatMessageContent message in chat.InvokeAsync(agent))
            {
                if (!string.IsNullOrWhiteSpace(message.Content))
                {
                    Console.WriteLine($"\n# {message.Role} - {message.AuthorName ?? "*"}: '{message.Content}'");
                }
            }
        }
    }
}
