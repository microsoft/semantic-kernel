// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;

namespace Agents;

/// <summary>
/// Demonstrate <see cref="ChatCompletionAgent"/> agent interacts with
/// <see cref="OpenAIAssistantAgent"/> when it produces image output.
/// </summary>
public class MixedChat_Images(ITestOutputHelper output) : BaseAgentsTest(output)
{
    /// <summary>
    /// Target OpenAI services.
    /// </summary>
    protected override bool ForceOpenAI => true;

    private const string AnalystName = "Analyst";
    private const string AnalystInstructions = "Create charts as requested without explanation.";

    private const string SummarizerName = "Summarizer";
    private const string SummarizerInstructions = "Summarize the entire conversation for the user in natural language.";

    [Fact]
    public async Task AnalyzeDataAndGenerateChartAsync()
    {
        OpenAIServiceConfiguration config = this.GetOpenAIConfiguration();

        FileClient fileClient = config.CreateFileClient();

        // Define the agents
        OpenAIAssistantAgent analystAgent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config,
                new()
                {
                    Instructions = AnalystInstructions,
                    Name = AnalystName,
                    EnableCodeInterpreter = true,
                    ModelId = this.Model,
                    Metadata = AssistantSampleMetadata,
                });

        ChatCompletionAgent summaryAgent =
            new()
            {
                Instructions = SummarizerInstructions,
                Name = SummarizerName,
                Kernel = this.CreateKernelWithChatCompletion(),
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
            await analystAgent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(Agent agent, string? input = null)
        {
            if (!string.IsNullOrWhiteSpace(input))
            {
                ChatMessageContent message = new(AuthorRole.User, input);
                chat.AddChatMessage(new(AuthorRole.User, input));
                this.WriteAgentChatMessage(message);
            }

            await foreach (ChatMessageContent response in chat.InvokeAsync(agent))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
