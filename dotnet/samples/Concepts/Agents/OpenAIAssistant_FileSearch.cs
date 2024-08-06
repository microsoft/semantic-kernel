// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using OpenAI.VectorStores;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate using retrieval on <see cref="OpenAIAssistantAgent"/> .
/// </summary>
public class OpenAIAssistant_FileSearch(ITestOutputHelper output) : BaseAgentsTest(output)
{
    /// <summary>
    /// Retrieval tool not supported on Azure OpenAI.
    /// </summary>
    protected override bool ForceOpenAI => true;

    [Fact]
    public async Task UseRetrievalToolWithOpenAIAssistantAgentAsync()
    {
        OpenAIServiceConfiguration config = this.GetOpenAIConfiguration();

        FileClient fileClient = config.CreateFileClient();

        OpenAIFileInfo uploadFile =
            await fileClient.UploadFileAsync(
                new BinaryData(await EmbeddedResource.ReadAllAsync("travelinfo.txt")!),
                "travelinfo.txt",
                FileUploadPurpose.Assistants);

        VectorStoreClient vectorStoreClient = config.CreateVectorStoreClient();
        VectorStoreCreationOptions vectorStoreOptions =
            new()
            {
                FileIds = [uploadFile.Id]
            };
        VectorStore vectorStore = await vectorStoreClient.CreateVectorStoreAsync(vectorStoreOptions);

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config,
                new()
                {
                    VectorStoreId = vectorStore.Id,
                    ModelId = this.Model,
                    Metadata = AssistantSampleMetadata,
                });

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

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
            await vectorStoreClient.DeleteVectorStoreAsync(vectorStore);
            await fileClient.DeleteFileAsync(uploadFile);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.AddChatMessage(new(AuthorRole.User, input));
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in chat.InvokeAsync(agent))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
