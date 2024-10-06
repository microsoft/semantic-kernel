<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
<<<<<<< HEAD
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.

>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
                kernel: new(),
                clientProvider: this.GetClientProvider(),
                new(this.Model)
=======
<<<<<<< HEAD
                kernel: new(),
                clientProvider: this.GetClientProvider(),
                new(this.Model)
=======
                clientProvider: this.GetClientProvider(),
                definition: new OpenAIAssistantDefinition(this.Model)
                {
                    EnableFileSearch = true,
                    Metadata = AssistantSampleMetadata,
                },
                kernel: new Kernel());
                kernel: new(),
                clientProvider: this.GetClientProvider(),
                definition: new OpenAIAssistantDefinition(this.Model)
>>>>>>> main
>>>>>>> Stashed changes
                {
                    EnableFileSearch = true,
                    Metadata = AssistantSampleMetadata,
                });
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
=======
=======
 6d73513a859ab2d05e01db3bc1d405827799e34b
                },
                kernel: new Kernel());

        // Upload file - Using a table of fictional employees.
        OpenAIFileClient fileClient = provider.Client.GetOpenAIFileClient();
        await using Stream stream = EmbeddedResource.ReadStream("employees.pdf")!;
        OpenAIFile fileInfo = await fileClient.UploadFileAsync(stream, "employees.pdf", FileUploadPurpose.Assistants);

        // Create a vector-store
        VectorStoreClient vectorStoreClient = provider.Client.GetVectorStoreClient();
        CreateVectorStoreOperation result =
            await vectorStoreClient.CreateVectorStoreAsync(waitUntilCompleted: false,
                new VectorStoreCreationOptions()
                {
                    FileIds = { fileInfo.Id },
>>>>>>> main
>>>>>>> Stashed changes
                    Metadata = { { AssistantSampleMetadataKey, bool.TrueString } }
                });

        // Create a thread associated with a vector-store for the agent conversation.
        string threadId =
            await agent.CreateThreadAsync(
                new OpenAIThreadCreationOptions
                {
<<<<<<< Updated upstream
                    VectorStoreId = vectorStore.Id,
=======
<<<<<<< HEAD
                    VectorStoreId = vectorStore.Id,
=======
                    VectorStoreId = result.VectorStoreId,
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
            await agent.DeleteAsync(CancellationToken.None);
=======
            await agent.DeleteAsync();
>>>>>>> main
            await vectorStoreClient.DeleteVectorStoreAsync(vectorStore);
<<<<<<< Updated upstream
=======
=======
            await agent.DeleteAsync(CancellationToken.None);
            await agent.DeleteAsync();
            await agent.DeleteAsync(CancellationToken.None);
 6d73513a859ab2d05e01db3bc1d405827799e34b
            await vectorStoreClient.DeleteVectorStoreAsync(vectorStore);
            await vectorStoreClient.DeleteVectorStoreAsync(result.VectorStoreId);
>>>>>>> main
>>>>>>> Stashed changes
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
