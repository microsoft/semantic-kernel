// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents.Bedrock;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> in the most basic way.
/// </summary>
public class Step01_BedrockAgent(ITestOutputHelper output) : BaseBedrockAgentTest(output)
{
    private const string UserQuery = "Why is the sky blue in one sentence?";

    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> and interact with it.
    /// The agent will respond to the user query.
    /// </summary>
    [Fact]
    public async Task UseNewAgentAsync()
    {
        // Create the agent
        var bedrock_agent = await this.CreateAgentAsync("Step01_BedrockAgent");

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

    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> and interact with it using streaming.
    /// The agent will respond to the user query.
    /// </summary>
    [Fact]
    public async Task UseNewAgentStreamingAsync()
    {
        // Create the agent
        var bedrock_agent = await this.CreateAgentAsync("Step01_BedrockAgent_Streaming");

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

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        return await BedrockAgent.CreateAsync(this.GetCreateAgentRequest(agentName));
    }
}
