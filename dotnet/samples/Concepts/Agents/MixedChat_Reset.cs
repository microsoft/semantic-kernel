// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;

/// <summary>
/// Demonstrate the use of <see cref="AgentChat.ResetAsync"/>.
/// </summary>
public class MixedChat_Reset(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    private const string AgentInstructions =
        """
        The user may either provide information or query on information previously provided.
        If the query does not correspond with information provided, inform the user that their query cannot be answered.
        """;

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ResetChat(bool useChatClient)
    {
        ChatCompletionAgent chatAgent =
            new()
            {
                Name = nameof(ChatCompletionAgent),
                Instructions = AgentInstructions,
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient),
            };

        // Define the Prompt Agent
        ProjectsAgentVersion promptAgent =
            await this.CreatePromptAgentAsync(
                "Recall",
                new DeclarativeAgentDefinition(DeploymentName) { Instructions = AgentInstructions });

        // Create the agent that uses the Prompt Agent
        ChatCompletionAgent promptAgentAgent =
            new()
            {
                Name = "FoundryPromptAgent",
                Kernel = this.CreateKernel(promptAgent),
            };

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input
        try
        {
            await InvokeAgentAsync(promptAgentAgent, "What is my favorite color?");
            await InvokeAgentAsync(chatAgent);

            await InvokeAgentAsync(promptAgentAgent, "I like green.");
            await InvokeAgentAsync(chatAgent);

            await InvokeAgentAsync(promptAgentAgent, "What is my favorite color?");
            await InvokeAgentAsync(chatAgent);

            await chat.ResetAsync();

            await InvokeAgentAsync(promptAgentAgent, "What is my favorite color?");
            await InvokeAgentAsync(chatAgent);
        }
        finally
        {
            await chat.ResetAsync();
            await this.DeletePromptAgentAsync(promptAgent);
        }

        chatClient?.Dispose();

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
