// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using FoundryAgent = Azure.AI.Projects.Agent;

namespace GettingStarted.AzureAgents;

/// <summary>
/// Demonstrate using code-interpreter on <see cref="AzureAIAgent"/> .
/// </summary>
public class Step09_AzureAIAgent_BingGrounding(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseBingGroundingToolWithAgent()
    {
        // Access the BingGrounding connection
        ConnectionsClient cxnClient = this.Client.GetConnectionsClient();
        ConnectionResponse bingConnection = await cxnClient.GetConnectionAsync(TestConfiguration.AzureAI.BingConnectionId);

        // Define the agent
        ToolConnectionList connectionList = new()
        {
            ConnectionList = { new ToolConnection(bingConnection.Id) }
        };
        FoundryAgent definition = await this.AgentsClient.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            tools: [new BingGroundingToolDefinition(connectionList)]);
        AzureAIAgent agent = new(definition, this.AgentsClient);

        // Create a thread for the agent conversation.
        AzureAIAgentThread thread = new(this.AgentsClient, metadata: SampleMetadata);

        // Respond to user input
        try
        {
            //await InvokeAgentAsync("How does wikipedia explain Euler's Identity?");
            await InvokeAgentAsync("What is the current price of gold?");
        }
        finally
        {
            await thread.DeleteAsync();
            await this.AgentsClient.DeleteAgentAsync(agent.Id);
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

    [Fact]
    public async Task UseBingGroundingToolWithStreaming()
    {
        // Access the BingGrounding connection
        ConnectionsClient cxnClient = this.Client.GetConnectionsClient();
        ConnectionResponse bingConnection = await cxnClient.GetConnectionAsync(TestConfiguration.AzureAI.BingConnectionId);

        // Define the agent
        ToolConnectionList connectionList = new()
        {
            ConnectionList = { new ToolConnection(bingConnection.Id) }
        };
        FoundryAgent definition = await this.AgentsClient.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            tools: [new BingGroundingToolDefinition(connectionList)]);
        AzureAIAgent agent = new(definition, this.AgentsClient);

        // Create a thread for the agent conversation.
        AzureAIAgentThread thread = new(this.AgentsClient, metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync("What is the current price of gold?");

            // Display chat history
            Console.WriteLine("\n================================");
            Console.WriteLine("CHAT HISTORY");
            Console.WriteLine("================================");

            await foreach (ChatMessageContent message in thread.GetMessagesAsync())
            {
                this.WriteAgentChatMessage(message);
            }
        }
        finally
        {
            await thread.DeleteAsync();
            await this.AgentsClient.DeleteAgentAsync(agent.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            bool isFirst = false;
            await foreach (StreamingChatMessageContent response in agent.InvokeStreamingAsync(message, thread))
            {
                if (!isFirst)
                {
                    Console.WriteLine($"\n# {response.Role} - {response.AuthorName ?? "*"}:");
                    isFirst = true;
                }

                if (!string.IsNullOrWhiteSpace(response.Content))
                {
                    Console.WriteLine($"\t> streamed: {response.Content}");
                }

                foreach (StreamingAnnotationContent? annotation in response.Items.OfType<StreamingAnnotationContent>())
                {
                    Console.WriteLine($"\t            {annotation.Url} - {annotation.Title}");
                }
            }
        }
    }
}
