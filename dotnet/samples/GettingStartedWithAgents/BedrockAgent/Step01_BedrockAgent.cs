// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.ChatCompletion;

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
    public async Task UseNewAgent()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step01_BedrockAgent");

        // Respond to user input
        AgentThread bedrockAgentThread = new BedrockAgentThread(this.RuntimeClient);
        try
        {
            var responses = bedrockAgent.InvokeAsync(new ChatMessageContent(AuthorRole.User, UserQuery), bedrockAgentThread, null);
            await foreach (ChatMessageContent response in responses)
            {
                this.Output.WriteLine(response.Content);
            }
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
            await bedrockAgentThread.DeleteAsync();
        }
    }

    /// <summary>
    /// Demonstrates how to use an existing <see cref="BedrockAgent"/> and interact with it.
    /// The agent will respond to the user query.
    /// </summary>
    [Fact]
    public async Task UseExistingAgent()
    {
        // Retrieve the agent
        // Replace "bedrock-agent-id" with the ID of the agent you want to use
        var agentId = "bedrock-agent-id";
        var getAgentResponse = await this.Client.GetAgentAsync(new() { AgentId = agentId });
        var bedrockAgent = new BedrockAgent(getAgentResponse.Agent, this.Client, this.RuntimeClient);

        // Respond to user input
        AgentThread bedrockAgentThread = new BedrockAgentThread(this.RuntimeClient);
        try
        {
            var responses = bedrockAgent.InvokeAsync(new ChatMessageContent(AuthorRole.User, UserQuery), bedrockAgentThread, null);
            await foreach (ChatMessageContent response in responses)
            {
                this.Output.WriteLine(response.Content);
            }
        }
        finally
        {
            await bedrockAgentThread.DeleteAsync();
        }
    }

    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> and interact with it using streaming.
    /// The agent will respond to the user query.
    /// </summary>
    [Fact]
    public async Task UseNewAgentStreaming()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step01_BedrockAgent_Streaming");
        AgentThread bedrockAgentThread = new BedrockAgentThread(this.RuntimeClient);

        // Respond to user input
        try
        {
            var streamingResponses = bedrockAgent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, UserQuery), bedrockAgentThread, null);
            await foreach (StreamingChatMessageContent response in streamingResponses)
            {
                this.Output.WriteLine(response.Content);
            }
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
            await bedrockAgentThread.DeleteAsync();
        }
    }

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        // Create a new agent on the Bedrock Agent service and prepare it for use
        var agentModel = await this.Client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest(agentName));
        // Create a new BedrockAgent instance with the agent model and the client
        // so that we can interact with the agent using Semantic Kernel contents.
        return new BedrockAgent(agentModel, this.Client, this.RuntimeClient);
    }
}
