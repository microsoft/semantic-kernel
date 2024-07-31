// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate <see cref="ChatCompletionAgent"/> agent interacts with
/// <see cref="OpenAIAssistantAgent"/> when it produces file output.
/// </summary>
public class MixedChat_Files(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Target OpenAI services.
    /// </summary>
    protected override bool ForceOpenAI => true;

    private const string SummaryInstructions = "Summarize the entire conversation for the user in natural language.";

    [Fact]
    public async Task AnalyzeFileAndGenerateReportAsync()
    {
        OpenAIServiceConfiguration config = GetOpenAIConfiguration();

        FileClient fileClient = config.CreateFileClient();

        OpenAIFileInfo uploadFile =
            await fileClient.UploadFileAsync(
                new BinaryData(await EmbeddedResource.ReadAllAsync("30-user-context.txt")),
                "30-user-context.txt",
                FileUploadPurpose.Assistants);

        Console.WriteLine(this.ApiKey);

        // Define the agents
        OpenAIAssistantAgent analystAgent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config,
                new()
                {
                    EnableCodeInterpreter = true, // Enable code-interpreter
                    ModelId = this.Model,
                    CodeInterpreterFileIds = [uploadFile.Id] // Associate uploaded file with assistant
                });

        ChatCompletionAgent summaryAgent =
            new()
            {
                Instructions = SummaryInstructions,
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
                Create a tab delimited file report of the ordered (descending) frequency distribution
                of words in the file '30-user-context.txt' for any words used more than once.
                """);
            await InvokeAgentAsync(summaryAgent);
        }
        finally
        {
            await analystAgent.DeleteAsync();
            await fileClient.DeleteFileAsync(uploadFile.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(Agent agent, string? input = null)
        {
            if (!string.IsNullOrWhiteSpace(input))
            {
                chat.AddChatMessage(new(AuthorRole.User, input));
                Console.WriteLine($"# {AuthorRole.User}: '{input}'");
            }

            await foreach (ChatMessageContent content in chat.InvokeAsync(agent))
            {
                Console.WriteLine($"\n# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");

                foreach (AnnotationContent annotation in content.Items.OfType<AnnotationContent>())
                {
                    Console.WriteLine($"\t* '{annotation.Quote}' => {annotation.FileId}");
                    BinaryData fileContent = await fileClient.DownloadFileAsync(annotation.FileId!);
                    Console.WriteLine($"\n{Encoding.Default.GetString(fileContent.ToArray())}");
                }
            }
        }
    }

    private OpenAIServiceConfiguration GetOpenAIConfiguration()
        =>
            this.UseOpenAIConfig ?
                OpenAIServiceConfiguration.ForOpenAI(this.ApiKey) :
                OpenAIServiceConfiguration.ForAzureOpenAI(this.ApiKey, new Uri(this.Endpoint!));
}
