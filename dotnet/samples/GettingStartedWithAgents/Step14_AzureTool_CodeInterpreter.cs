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
public class Step14_AzureTool_CodeInterpreter(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseCodeInterpreterToolWithAgentAsync()
    {
        // Define the agent
        AzureAIClientProvider clientProvider = this.GetAzureProvider();
        AzureAIP.AgentsClient client = clientProvider.Client.GetAgentsClient();
        AzureAIP.Agent definition = await client.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            tools: [new AzureAIP.CodeInterpreterToolDefinition()]);
        AzureAIAgent agent = new(definition, clientProvider)
        {
            Kernel = new Kernel(),
        };

        // Create a thread for the agent conversation.
        AgentThread thread = await client.CreateThreadAsync(metadata: AssistantSampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?");
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
