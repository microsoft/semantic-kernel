// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
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
        OpenAIFileService fileService = new(TestConfiguration.OpenAI.ApiKey);
        OpenAIFileReference uploadFile =
            await fileService.UploadContentAsync(
                new BinaryContent(await EmbeddedResource.ReadAllAsync("sales.csv"), mimeType: "text/plain"),
                new OpenAIFileUploadExecutionSettings("sales.csv", OpenAIFilePurpose.Assistants));

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
            await fileService.DeleteFileAsync(uploadFile.Id);
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
                    BinaryContent fileContent = await fileService.GetFileContentAsync(annotation.FileId!);
                    byte[] byteContent = fileContent.Data?.ToArray() ?? [];
                    Console.WriteLine(Encoding.Default.GetString(byteContent));
                }
            }
        }
    }

    private OpenAIConfiguration GetOpenAIConfiguration()
        =>
            this.UseOpenAIConfig ?
                OpenAIConfiguration.ForOpenAI(this.ApiKey) :
                OpenAIConfiguration.ForAzureOpenAI(this.ApiKey, new Uri(this.Endpoint!));
}
