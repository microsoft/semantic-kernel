// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Agents;

/// <summary>
/// Demonstrate <see cref="ChatCompletionAgent"/> agent interacts with
/// <see cref="OpenAIAssistantAgent"/> when it produces image output.
/// </summary>
public class MixedChat_Images(ITestOutputHelper output) : BaseTest(output)
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
        OpenAIFileService fileService = new(TestConfiguration.OpenAI.ApiKey);

        // Define the agents
        OpenAIAssistantAgent analystAgent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config: new(this.ApiKey, this.Endpoint),
                new()
                {
                    Instructions = AnalystInstructions,
                    Name = AnalystName,
                    EnableCodeInterpreter = true,
                    ModelId = this.Model,
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
                chat.AddChatMessage(new(AuthorRole.User, input));
                Console.WriteLine($"# {AuthorRole.User}: '{input}'");
            }

            await foreach (ChatMessageContent message in chat.InvokeAsync(agent))
            {
                if (!string.IsNullOrWhiteSpace(message.Content))
                {
                    Console.WriteLine($"\n# {message.Role} - {message.AuthorName ?? "*"}: '{message.Content}'");
                }

                foreach (FileReferenceContent fileReference in message.Items.OfType<FileReferenceContent>())
                {
                    Console.WriteLine($"\t* Generated image - @{fileReference.FileId}");
                    BinaryContent fileContent = await fileService.GetFileContentAsync(fileReference.FileId!);
                    byte[] byteContent = fileContent.Data?.ToArray() ?? [];
                    string filePath = Path.ChangeExtension(Path.GetTempFileName(), ".png");
                    await File.WriteAllBytesAsync($"{filePath}.png", byteContent);
                    Console.WriteLine($"\t* Local path - {filePath}");
                }
            }
        }
    }
}
