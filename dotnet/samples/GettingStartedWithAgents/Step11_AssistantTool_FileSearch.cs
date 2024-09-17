﻿// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using OpenAI.VectorStores;
using Resources;

namespace GettingStarted;

/// <summary>
/// Demonstrate using code-interpreter on <see cref="OpenAIAssistantAgent"/> .
/// </summary>
public class Step11_AssistantTool_FileSearch(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseFileSearchToolWithAssistantAgentAsync()
    {
        // Define the agent
        OpenAIClientProvider provider = this.GetClientProvider();
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                clientProvider: this.GetClientProvider(),
                new(this.Model)
                {
                    EnableFileSearch = true,
                    Metadata = AssistantSampleMetadata,
                });

        // Upload file - Using a table of fictional employees.
        FileClient fileClient = provider.Client.GetFileClient();
        await using Stream stream = EmbeddedResource.ReadStream("employees.pdf")!;
        OpenAIFileInfo fileInfo = await fileClient.UploadFileAsync(stream, "employees.pdf", FileUploadPurpose.Assistants);

        // Create a vector-store
        VectorStoreClient vectorStoreClient = provider.Client.GetVectorStoreClient();
        VectorStore vectorStore =
            await vectorStoreClient.CreateVectorStoreAsync(
                new VectorStoreCreationOptions()
                {
                    FileIds = [fileInfo.Id],
                    Metadata = { { AssistantSampleMetadataKey, bool.TrueString } }
                });

        // Create a thread associated with a vector-store for the agent conversation.
        string threadId =
            await agent.CreateThreadAsync(
                new OpenAIThreadCreationOptions
                {
                    VectorStoreId = vectorStore.Id,
                    Metadata = AssistantSampleMetadata,
                });

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Who is the youngest employee?");
            await InvokeAgentAsync("Who works in sales?");
            await InvokeAgentAsync("I have a customer request, who can help me?");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
            await vectorStoreClient.DeleteVectorStoreAsync(vectorStore);
            await fileClient.DeleteFileAsync(fileInfo.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            await agent.AddChatMessageAsync(threadId, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(threadId))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
