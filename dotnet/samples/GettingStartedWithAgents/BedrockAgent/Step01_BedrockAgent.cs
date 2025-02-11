// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockAgent.Model;
using Microsoft.SemanticKernel.Agents.Bedrock;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> in the most basic way.
/// </summary>
public class Step01_BedrockAgent(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string AgentName = "Semantic-Kernel-Test-Agent";
    private const string AgentDescription = "A helpful assistant who helps users find information.";
    private const string AgentInstruction = "You're a helpful assistant who helps users find information.";
    private const string UserQuery = "Why is the sky blue?";

    [Fact]
    public async Task UseNewAgentAsync()
    {
        // Define the agent
        CreateAgentRequest createAgentRequest = new()
        {
            AgentName = AgentName,
            Description = AgentDescription,
            Instruction = AgentInstruction,
            AgentResourceRoleArn = TestConfiguration.BedrockAgent.AgentResourceRoleArn,
            FoundationModel = TestConfiguration.BedrockAgent.FoundationModel,
        };

        var bedrock_agent = await BedrockAgent.CreateAsync(createAgentRequest);

        // Respond to user input
        try
        {
            var responses = bedrock_agent.InvokeAsync(BedrockAgent.CreateSessionId(), UserQuery, null, CancellationToken.None);
            await foreach (var response in responses)
            {
                this.Output.WriteLine(response.Content);
            }
        }
        finally
        {
            await bedrock_agent.DeleteAsync(CancellationToken.None);
        }
    }

    [Fact]
    public async Task UseNewAgentStreamingAsync()
    {
        // Define the agent
        CreateAgentRequest createAgentRequest = new()
        {
            AgentName = AgentName,
            Description = AgentDescription,
            Instruction = AgentInstruction,
            AgentResourceRoleArn = TestConfiguration.BedrockAgent.AgentResourceRoleArn,
            FoundationModel = TestConfiguration.BedrockAgent.FoundationModel,
        };

        var bedrock_agent = await BedrockAgent.CreateAsync(createAgentRequest);

        // Respond to user input
        try
        {
            var streamingResponses = bedrock_agent.InvokeStreamingAsync(BedrockAgent.CreateSessionId(), UserQuery, null, CancellationToken.None);
            await foreach (var response in streamingResponses)
            {
                this.Output.WriteLine(response.Content);
            }
        }
        finally
        {
            await bedrock_agent.DeleteAsync(CancellationToken.None);
        }
    }

    [Fact]
    public async Task UseTemplateForAssistantAgentAsync()
    {
        // Define the agent

        // Instructions, Name and Description properties defined via the config.

        // Create a thread for the agent conversation.

        // Local function to invoke agent and display the response.
    }
}
