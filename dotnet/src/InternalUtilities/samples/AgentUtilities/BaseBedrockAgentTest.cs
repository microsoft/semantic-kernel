// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;
using Amazon.BedrockAgentRuntime;
using Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Base class for samples that demonstrate the usage of AWS Bedrock agents.
/// </summary>
public abstract class BaseBedrockAgentTest : BaseAgentsTest
{
    protected const string AgentDescription = "A helpful assistant who helps users find information.";
    protected const string AgentInstruction = "You're a helpful assistant who helps users find information.";
    protected readonly AmazonBedrockAgentClient Client;
    protected readonly AmazonBedrockAgentRuntimeClient RuntimeClient;

    protected BaseBedrockAgentTest(ITestOutputHelper output) : base(output)
    {
        Client = new AmazonBedrockAgentClient();
        RuntimeClient = new AmazonBedrockAgentRuntimeClient();
    }

    protected CreateAgentRequest GetCreateAgentRequest(string agentName) => new()
    {
        AgentName = agentName,
        Description = AgentDescription,
        Instruction = AgentInstruction,
        AgentResourceRoleArn = TestConfiguration.BedrockAgent.AgentResourceRoleArn,
        FoundationModel = TestConfiguration.BedrockAgent.FoundationModel,
    };

    protected override void Dispose(bool disposing)
    {
        Client?.Dispose();
        RuntimeClient?.Dispose();
        base.Dispose(disposing);
    }

    /// <summary>
    /// Override this method to create an agent with desired settings.
    /// </summary>
    /// <param name="agentName">The name of the agent to create. Must be unique.</param>
    protected abstract Task<BedrockAgent> CreateAgentAsync(string agentName);
}
