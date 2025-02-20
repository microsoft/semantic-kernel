// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Agent = Azure.AI.Projects.Agent;

namespace GettingStarted.AzureAgents;

/// <summary>
/// Demonstrate using code-interpreter on <see cref="AzureAIAgent"/> .
/// </summary>
public class Step04_AzureAIAgent_CodeInterpreter(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseCodeInterpreterToolWithAgentAsync()
    {
        // Define the agent
        Agent definition = await this.AgentsClient.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            tools: [new CodeInterpreterToolDefinition()]);
        AzureAIAgent agent = new(definition, this.AgentsClient)
        {
            Kernel = new Kernel(),
        };

        // Create a thread for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?");
        }
        finally
        {
            await this.AgentsClient.DeleteThreadAsync(thread.Id);
            await this.AgentsClient.DeleteAgentAsync(agent.Id);
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
