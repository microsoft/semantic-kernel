// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;

/// <summary>
/// Demonstrate the use of <see cref="AgentChat.ResetAsync"/>.
/// </summary>
public class MixedChat_Reset(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string AgentInstructions =
        """
        The user may either provide information or query on information previously provided.
        If the query does not correspond with information provided, inform the user that their query cannot be answered.
        """;

    [Fact]
    public async Task ResetChatAsync()
    {
        OpenAIClientProvider provider = this.GetClientProvider();

        // Define the agents
        OpenAIAssistantAgent assistantAgent =
            await OpenAIAssistantAgent.CreateAsync(
                provider,
                definition: new OpenAIAssistantDefinition(this.Model)
                {
                    Name = nameof(OpenAIAssistantAgent),
                    Instructions = AgentInstructions,
                },
                kernel: new Kernel());

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
                ChatMessageContent message = new(AuthorRole.User, input);
                chat.AddChatMessage(message);
                this.WriteAgentChatMessage(message);
            }

            await foreach (ChatMessageContent response in chat.InvokeAsync(agent))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
