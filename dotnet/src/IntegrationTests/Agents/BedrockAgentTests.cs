// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.Agents.Bedrock.Extensions;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class BedrockAgentTests : IDisposable
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<BedrockAgentTests>()
        .Build();

    private readonly AmazonBedrockAgentClient _client = new();

    /// <summary>
    /// Integration test for creating a <see cref="BedrockAgent"/>.
    /// </summary>
    // [Theory(Skip = "This test is for manual verification.")]
    [Theory()]
    [InlineData("Why is the sky blue in one sentence?")]
    public async Task InvokeTestAsync(string input)
    {
        var agentModel = await this._client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest());
        var bedrockAgent = new BedrockAgent(agentModel, this._client);

        try
        {
            await this.ExecuteAgentAsync(bedrockAgent, input);
        }
        finally
        {
            await this._client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    /// <summary>
    /// Executes a <see cref="BedrockAgent"/> with the specified input and expected output.
    /// The output of the agent will be verified against the expected output.
    /// If the expected output is not provided, the verification will pass as long as the output is not null or empty.
    /// </summary>
    /// <param name="agent">The agent to execute.</param>
    /// <param name="input">The input to provide to the agent.</param>
    /// <param name="expected">The expected output from the agent.</param>
    private async Task ExecuteAgentAsync(BedrockAgent agent, string input, string? expected = null)
    {
        var responses = agent.InvokeAsync(BedrockAgent.CreateSessionId(), input, null, default);
        string responseContent = string.Empty;
        await foreach (var response in responses)
        {
            // Non-streaming invoke will only return one response.
            responseContent = response.Content ?? string.Empty;
        }

        if (expected != null)
        {
            Assert.Contains(expected, responseContent);
        }
        else
        {
            Assert.False(string.IsNullOrEmpty(responseContent));
        }
    }

    private const string AgentName = "SKIntegrationTestAgent";
    private const string AgentDescription = "A helpful assistant who helps users find information.";
    private const string AgentInstruction = "You're a helpful assistant who helps users find information.";
    private CreateAgentRequest GetCreateAgentRequest()
    {
        BedrockAgentConfiguration bedrockAgentSettings = this._configuration.GetSection("BedrockAgent").Get<BedrockAgentConfiguration>()!;
        Assert.NotNull(bedrockAgentSettings);

        return new()
        {
            AgentName = AgentName,
            Description = AgentDescription,
            Instruction = AgentInstruction,
            AgentResourceRoleArn = bedrockAgentSettings.AgentResourceRoleArn,
            FoundationModel = bedrockAgentSettings.FoundationModel,
        };
    }

    public void Dispose()
    {
        this._client.Dispose();
    }
}