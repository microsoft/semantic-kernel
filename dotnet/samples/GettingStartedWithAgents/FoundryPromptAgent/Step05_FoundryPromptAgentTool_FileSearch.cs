// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using OpenAI.Responses;
using OpenAI.VectorStores;
using Resources;

namespace GettingStarted.FoundryPromptAgents;

/// <summary>
/// Demonstrate using a Microsoft Foundry Prompt Agent with file search.
/// </summary>
public class Step05_FoundryPromptAgentTool_FileSearch(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    private static readonly TimeSpan s_indexingTimeout = TimeSpan.FromMinutes(2);

    [Fact]
    public async Task UseFileSearchToolWithFoundryPromptAgent()
    {
        // Upload file - Using a table of fictional employees.
        await using Stream stream = EmbeddedResource.ReadStream("employees.pdf")!;
        OpenAIFile file = await this.UploadFileAsync(stream, "employees.pdf");

        VectorStore? vectorStore = null;
        ProjectsAgentVersion? promptAgent = null;

        try
        {
            // Create a vector-store
            vectorStore =
                (await this.VectorStoreClient.CreateVectorStoreAsync(
                    new VectorStoreCreationOptions()
                    {
                        Name = "step5_employees",
                        FileIds = { file.Id },
                    })).Value;

            // The vector-store indexes its files in the background. Wait for indexing to finish,
            // so the first question isn't answered from an empty or partially indexed store.
            await this.WaitForVectorStoreAsync(vectorStore.Id);

            // Define the Prompt Agent with the file-search tool associated with the vector-store.
            DeclarativeAgentDefinition definition = new(DeploymentName);
            definition.Tools.Add(ResponseTool.CreateFileSearchTool([vectorStore.Id]));
            promptAgent = await this.CreatePromptAgentAsync("Search", definition);

            // Create the agent
            ChatCompletionAgent agent =
                new()
                {
                    Kernel = this.CreateKernel(promptAgent),
                };

            // Create a thread for the agent conversation.
            AgentThread thread = new ChatHistoryAgentThread();

            // Respond to user input
            await InvokeAgentAsync(agent, thread, "Who is the youngest employee?");
            await InvokeAgentAsync(agent, thread, "Who works in sales?");
            await InvokeAgentAsync(agent, thread, "I have a customer request, who can help me?");

            await thread.DeleteAsync();
        }
        finally
        {
            if (promptAgent is not null)
            {
                await this.DeletePromptAgentAsync(promptAgent);
            }

            if (vectorStore is not null)
            {
                await this.VectorStoreClient.DeleteVectorStoreAsync(vectorStore.Id);
            }

            await this.FileClient.DeleteFileAsync(file.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(ChatCompletionAgent agent, AgentThread thread, string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }

    private async Task WaitForVectorStoreAsync(string vectorStoreId)
    {
        using CancellationTokenSource timeout = new(s_indexingTimeout);

        while (true)
        {
            VectorStore vectorStore = (await this.VectorStoreClient.GetVectorStoreAsync(vectorStoreId, timeout.Token)).Value;

            if (vectorStore.Status != VectorStoreStatus.InProgress)
            {
                // A completed store can still contain files that failed to index, and those files would be missing from every answer.
                if (vectorStore.Status != VectorStoreStatus.Completed || vectorStore.FileCounts.Failed > 0)
                {
                    throw new InvalidOperationException($"Vector store {vectorStoreId} finished with status {vectorStore.Status} and {vectorStore.FileCounts.Failed} failed file(s).");
                }

                return;
            }

            await Task.Delay(TimeSpan.FromSeconds(1), timeout.Token);
        }
    }
}
