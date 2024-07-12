// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;
using OpenAI.Files;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate using code-interpreter to manipulate and generate csv files with <see cref="OpenAIAssistantAgent"/> .
/// </summary>
public class OpenAIAssistant_FileManipulation(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Target OpenAI services.
    /// </summary>
    protected override bool ForceOpenAI => true;

    [Fact]
    public async Task AnalyzeCSVFileUsingOpenAIAssistantAgentAsync()
    {
        FileClient fileClient = CreateFileClient();

        OpenAIFileInfo uploadFile =
            await fileClient.UploadFileAsync(
                new BinaryData(await EmbeddedResource.ReadAllAsync("sales.csv")!),
                "sales.csv",
                FileUploadPurpose.Assistants);

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config: GetOpenAIConfiguration(),
                new()
                {
                    CodeInterpterFileIds = [uploadFile.Id],
                    EnableCodeInterpreter = true, // Enable code-interpreter
                    ModelName = this.Model,
                });

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Which segment had the most sales?");
            await InvokeAgentAsync("List the top 5 countries that generated the most profit.");
            await InvokeAgentAsync("Create a tab delimited file report of profit by each country per month.");
        }
        finally
        {
            await agent.DeleteAsync();
            await fileClient.DeleteFileAsync(uploadFile.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            chat.AddChatMessage(new(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (ChatMessageContent message in chat.InvokeAsync(agent))
            {
                Console.WriteLine($"# {message.Role} - {message.AuthorName ?? "*"}: '{message.Content}'");

                foreach (AnnotationContent annotation in message.Items.OfType<AnnotationContent>())
                {
                    Console.WriteLine($"\n* '{annotation.Quote}' => {annotation.FileId}");
                    BinaryData content = await fileClient.DownloadFileAsync(annotation.FileId!);
                    Console.WriteLine(Encoding.Default.GetString(content.ToArray()));
                }
            }
        }
    }

    private OpenAIServiceConfiguration GetOpenAIConfiguration()
        =>
            this.UseOpenAIConfig ?
                OpenAIServiceConfiguration.ForOpenAI(this.ApiKey) :
                OpenAIServiceConfiguration.ForAzureOpenAI(this.ApiKey, new Uri(this.Endpoint!));

    private FileClient CreateFileClient()
    {
        OpenAIClient client =
            this.ForceOpenAI || string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint) ?
                new OpenAIClient(TestConfiguration.OpenAI.ApiKey) :
                new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAI.Endpoint), TestConfiguration.AzureOpenAI.ApiKey);

        return client.GetFileClient();
    }
}
