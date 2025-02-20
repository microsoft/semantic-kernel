// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;
using Agent = Azure.AI.Projects.Agent;

namespace GettingStarted.AzureAgents;

/// <summary>
/// Demonstrate using <see cref="AzureAIAgent"/> with file search.
/// </summary>
public class Step05_AzureAIAgent_FileSearch(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseFileSearchToolWithAgentAsync()
    {
        // Define the agent
        await using Stream stream = EmbeddedResource.ReadStream("employees.pdf")!;

        AgentFile fileInfo = await this.AgentsClient.UploadFileAsync(stream, AgentFilePurpose.Agents, "employees.pdf");
        VectorStore fileStore =
            await this.AgentsClient.CreateVectorStoreAsync(
                [fileInfo.Id],
                metadata: new Dictionary<string, string>() { { SampleMetadataKey, bool.TrueString } });
        Agent agentModel = await this.AgentsClient.CreateAgentAsync(
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
        AzureAIAgent agent = new(agentModel, this.AgentsClient);

        // Create a thread associated for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Who is the youngest employee?");
            await InvokeAgentAsync("Who works in sales?");
            await InvokeAgentAsync("I have a customer request, who can help me?");
        }
        finally
        {
            await this.AgentsClient.DeleteThreadAsync(thread.Id);
            await this.AgentsClient.DeleteAgentAsync(agent.Id);
            await this.AgentsClient.DeleteVectorStoreAsync(fileStore.Id);
            await this.AgentsClient.DeleteFileAsync(fileInfo.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            await agent.AddChatMessageAsync(thread.Id, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(thread.Id))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
