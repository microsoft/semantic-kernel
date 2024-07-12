// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;
using OpenAI.Files;
using OpenAI.VectorStores;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate using retrieval on <see cref="OpenAIAssistantAgent"/> .
/// </summary>
public class OpenAIAssistant_FileSearch(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Retrieval tool not supported on Azure OpenAI.
    /// </summary>
    protected override bool ForceOpenAI => true;

    [Fact]
    public async Task UseRetrievalToolWithOpenAIAssistantAgentAsync()
    {
        FileClient fileClient = CreateFileClient();

        OpenAIFileInfo uploadFile =
            await fileClient.UploadFileAsync(
                new BinaryData(await EmbeddedResource.ReadAllAsync("travelinfo.txt")!),
                "travelinfo.txt",
                FileUploadPurpose.Assistants);

        VectorStore vectorStore =
            await new OpenAIVectorStoreBuilder(GetOpenAIConfiguration())
                .AddFile(uploadFile.Id)
                .CreateAsync();

        OpenAIVectorStore openAIStore = new(vectorStore.Id, GetOpenAIConfiguration());

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config: GetOpenAIConfiguration(),
                new()
                {
                    ModelName = this.Model,
                    VectorStoreId = vectorStore.Id,
                });

        // Create a chat for agent interaction.
        var chat = new AgentGroupChat();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Where did sam go?");
            await InvokeAgentAsync("When does the flight leave Seattle?");
            await InvokeAgentAsync("What is the hotel contact info at the destination?");
        }
        finally
        {
            await agent.DeleteAsync();
            await openAIStore.DeleteAsync();
            await fileClient.DeleteFileAsync(uploadFile.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var content in chat.InvokeAsync(agent))
            {
                Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
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
