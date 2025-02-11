// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockAgent.Model;
using Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Base class for samples that demonstrate the usage of agents.
/// </summary>
public abstract class BaseBedrockAgentTest(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    protected const string AgentDescription = "A helpful assistant who helps users find information.";
    protected const string AgentInstruction = "You're a helpful assistant who helps users find information.";

    protected CreateAgentRequest GetCreateAgentRequest(string agentName) => new()
    {
        AgentName = agentName,
        Description = AgentDescription,
        Instruction = AgentInstruction,
        AgentResourceRoleArn = TestConfiguration.BedrockAgent.AgentResourceRoleArn,
        FoundationModel = TestConfiguration.BedrockAgent.FoundationModel,
    };

    /// <summary>
    /// Create a new <see cref="BedrockAgent"/> instance.
    /// Override this method to create an agent with desired settings.
    /// </summary>
    /// <param name="agentName">The name of the agent to create. Must be unique.</param>
    protected abstract Task<BedrockAgent> CreateAgentAsync(string agentName);
}