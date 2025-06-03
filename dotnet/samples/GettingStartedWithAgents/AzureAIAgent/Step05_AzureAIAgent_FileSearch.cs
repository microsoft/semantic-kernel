// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace GettingStarted.AzureAgents;

/// <summary>
/// Demonstrate using <see cref="AzureAIAgent"/> with file search.
/// </summary>
public class Step05_AzureAIAgent_FileSearch(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseFileSearchToolWithAgent()
    {
        // Define the agent
        await using Stream stream = EmbeddedResource.ReadStream("employees.pdf")!;

        PersistentAgentFileInfo fileInfo = await this.Client.Files.UploadFileAsync(stream, PersistentAgentFilePurpose.Agents, "employees.pdf");
        PersistentAgentsVectorStore fileStore =
            await this.Client.VectorStores.CreateVectorStoreAsync(
                [fileInfo.Id],
                metadata: new Dictionary<string, string>() { { SampleMetadataKey, bool.TrueString } });
        PersistentAgent agentModel = await this.Client.Administration.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            tools: [new FileSearchToolDefinition()],
            toolResources: new()
            {
                FileSearch = new()
                {
                    VectorStoreIds = { fileStore.Id },
                }
            },
            metadata: new Dictionary<string, string>() { { SampleMetadataKey, bool.TrueString } });
        AzureAIAgent agent = new(agentModel, this.Client);

        // Create a thread associated for the agent conversation.
        Microsoft.SemanticKernel.Agents.AgentThread thread = new AzureAIAgentThread(this.Client, metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Who is the youngest employee?");
            await InvokeAgentAsync("Who works in sales?");
            await InvokeAgentAsync("I have a customer request, who can help me?");
        }
        finally
        {
            await thread.DeleteAsync();
            await this.Client.Administration.DeleteAgentAsync(agent.Id);
            await this.Client.VectorStores.DeleteVectorStoreAsync(fileStore.Id);
            await this.Client.Files.DeleteFileAsync(fileInfo.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
