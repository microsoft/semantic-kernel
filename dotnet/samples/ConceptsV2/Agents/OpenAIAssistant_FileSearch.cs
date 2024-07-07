// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using OpenAI;
using Resources;
using OpenAI.VectorStores;

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
        OpenAIClient rootClient = OpenAIClientFactory.CreateClient(GetOpenAIConfiguration()); // %%% HACK
        FileClient fileClient = rootClient.GetFileClient();

        Stream fileStream = EmbeddedResource.ReadStream("travelinfo.txt")!; // %%% USING
        OpenAIFileInfo fileInfo =
            await fileClient.UploadFileAsync(
                    fileStream,
                    "travelinfo.txt",
                    FileUploadPurpose.Assistants);

        VectorStore vectorStore =
            await new OpenAIVectorStoreBuilder(GetOpenAIConfiguration())
                .AddFile(fileInfo.Id)
                .CreateAsync();

        OpenAIVectorStore openAIStore = new(vectorStore.Id, GetOpenAIConfiguration());

        //OpenAIFileService fileService = new(TestConfiguration.OpenAI.ApiKey); // %%% USE THIS
        //OpenAIFileReference uploadFile =
        //    await fileService.UploadContentAsync(new BinaryContent(await EmbeddedResource.ReadAllAsync("travelinfo.txt")!, "text/plain"),
        //        new OpenAIFileUploadExecutionSettings("travelinfo.txt", OpenAIFilePurpose.Assistants));

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

    private OpenAIConfiguration GetOpenAIConfiguration()
        =>
            this.UseOpenAIConfig ?
                OpenAIConfiguration.ForOpenAI(this.ApiKey) :
                OpenAIConfiguration.ForAzureOpenAI(this.ApiKey, new Uri(this.Endpoint!));
}
