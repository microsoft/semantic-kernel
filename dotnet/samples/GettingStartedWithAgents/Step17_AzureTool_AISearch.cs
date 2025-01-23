// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using AzureAIP = Azure.AI.Projects;

namespace GettingStarted;

/// <summary>
/// Demonstrate using code-interpreter on <see cref="AzureAIAgent"/> .
/// </summary>
public class Step17_AzureTool_AISearch(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseAISearchToolWithAgentAsync()
    {
        // Define the agent
        AzureAIClientProvider clientProvider = this.GetAzureProvider();
        AzureAIP.ConnectionsClient cxnClient = clientProvider.Client.GetConnectionsClient();
        AzureAIP.ListConnectionsResponse searchConnections = await cxnClient.GetConnectionsAsync(AzureAIP.ConnectionType.AzureAISearch);
        AzureAIP.ConnectionResponse searchConnection = searchConnections.Value[0]; // $$$ Duplicate resources

        AzureAIP.AgentsClient client = clientProvider.Client.GetAgentsClient();
        AzureAIP.Agent agentModel = await client.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            tools: [new AzureAIP.AzureAISearchToolDefinition()],
            toolResources: new()
            {
                AzureAISearch = new()
                {
                    IndexList = { new AzureAIP.IndexResource(searchConnection.Id, "recipies") }
                }
            });
        AzureAIAgent agent = new(agentModel, clientProvider);

        // Create a thread associated with a vector-store for the agent conversation.
        AgentThread thread = await client.CreateThreadAsync(metadata: AssistantSampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync("What recipie can I make that uses cinnamon?");
            await InvokeAgentAsync("List the drink recipies available?");
        }
        finally
        {
            await client.DeleteThreadAsync(thread.Id);
            await client.DeleteAgentAsync(agent.Id);
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
