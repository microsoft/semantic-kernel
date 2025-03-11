// Copyright (c) Microsoft. All rights reserved.
using Amazon.BedrockAgent;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to declaratively create instances of <see cref="BedrockAgent"/>.
/// </summary>
public class Step07_BedrockAgent_Declarative : BaseBedrockAgentTest
{
    public Step07_BedrockAgent_Declarative(ITestOutputHelper output) : base(output)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<AmazonBedrockAgentClient>(this.Client);
        this._kernel = builder.Build();
    }

    [Fact]
    public async Task BedrockAgentWithConfigurationAsync()
    {
        var text =
            $"""
            type: bedrock_agent
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: {TestConfiguration.BedrockAgent.FoundationModel}
              configuration:
                type: bedrock
                agent_resource_role_arn: {TestConfiguration.BedrockAgent.AgentResourceRoleArn}
            """;
        BedrockAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text) as BedrockAgent;

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    [Fact]
    public async Task BedrockAgentWithKernelAsync()
    {
        var text =
            $"""
            type: bedrock_agent
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: {TestConfiguration.BedrockAgent.FoundationModel}
            """;
        BedrockAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as BedrockAgent;

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        // Create a new agent on the Bedrock Agent service and prepare it for use
        var agentModel = await this.Client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest(agentName));
        // Create a new BedrockAgent instance with the agent model and the client
        // so that we can interact with the agent using Semantic Kernel contents.
        return new BedrockAgent(agentModel, this.Client, this.RuntimeClient);
    }

    #region private
    private readonly Kernel _kernel;

    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(BedrockAgent agent, string input)
    {
        // Create a thread for the agent conversation.
        string sessionId = BedrockAgent.CreateSessionId();

        try
        {
            await InvokeAgentAsync(input);
        }
        finally
        {
            await agent.Client.DeleteAgentAsync(new() { AgentId = agent.Id });
        }

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(string input)
        {
            await foreach (ChatMessageContent response in agent.InvokeAsync(sessionId, input, null))
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
    }
    #endregion
}
