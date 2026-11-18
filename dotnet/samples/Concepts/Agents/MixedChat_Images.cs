// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace Agents;

/// <summary>
/// Demonstrate <see cref="ChatCompletionAgent"/> agent interacts with
/// an agent that uses a Microsoft Foundry Prompt Agent when it produces image output.
/// </summary>
public class MixedChat_Images(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    private const string AnalystName = "Analyst";
    private const string AnalystInstructions = "Create charts as requested without explanation.";

    private const string SummarizerName = "Summarizer";
    private const string SummarizerInstructions = "Summarize the entire conversation for the user in natural language.";

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task AnalyzeDataAndGenerateChartAsync(bool useChatClient)
    {
        ChatCompletionAgent summaryAgent =
            new()
            {
                Instructions = SummarizerInstructions,
                Name = SummarizerName,
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient),
            };

        // Define the Prompt Agent with the code-interpreter tool.
        DeclarativeAgentDefinition definition = new(DeploymentName)
        {
            Instructions = AnalystInstructions,
        };
        definition.Tools.Add(
            ResponseTool.CreateCodeInterpreterTool(
                new CodeInterpreterToolContainer(
                    CodeInterpreterToolContainerConfiguration.CreateAutomaticContainerConfiguration())));
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync(AnalystName, definition);

        // Create the agent that uses the Prompt Agent
        ChatCompletionAgent analystAgent =
            new()
            {
                Name = AnalystName,
                Kernel = this.CreateKernel(promptAgent),
            };

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input
        try
        {
            await InvokeAgentAsync(
                analystAgent,
                """
                Graph the percentage of storm events by state using a pie chart:

                State, StormCount
                TEXAS, 4701
                KANSAS, 3166
                IOWA, 2337
                ILLINOIS, 2022
                MISSOURI, 2016
                GEORGIA, 1983
                MINNESOTA, 1881
                WISCONSIN, 1850
                NEBRASKA, 1766
                NEW YORK, 1750
                """);

            await InvokeAgentAsync(summaryAgent);
        }
        finally
        {
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
                await this.DownloadGeneratedFilesAsync(response, launchViewer: true);
            }
        }
    }
}
