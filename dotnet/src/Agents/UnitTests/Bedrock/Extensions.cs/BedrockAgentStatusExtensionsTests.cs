// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;
using Amazon.BedrockAgentRuntime;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.Agents.Bedrock.Extensions;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Bedrock.Extensions;

/// <summary>
/// Unit testing of <see cref="BedrockAgentStatusExtensions"/>.
/// </summary>
public class BedrockAgentStatusExtensionsTests
{
    private readonly Amazon.BedrockAgent.Model.Agent _agentModel = new()
    {
        AgentId = "1234567890",
        AgentName = "testName",
        Description = "test description",
        Instruction = "Instruction must have at least 40 characters",
    };

    /// <summary>
    /// Verify the waiting for the agent to reach the specified status.
    /// </summary>
    [Fact]
    public async Task VerifyWaitForAgentStatusAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        BedrockAgent agent = new(this._agentModel, mockClient.Object, mockRuntimeClient.Object);

        // Act
        await agent.WaitForAgentStatusAsync(AgentStatus.PREPARED, CancellationToken.None, 1, 2);

        // Assert
        mockClient.Verify(x => x.GetAgentAsync(It.IsAny<GetAgentRequest>(), default), Times.Exactly(2));
    }

    /// <summary>
    /// Verify the extension throws an exception when the agent does not reach the specified
    /// status within the specified time.
    /// </summary>
    [Fact]
    public async Task VerifyWaitForAgentStatusThrowAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        BedrockAgent agent = new(this._agentModel, mockClient.Object, mockRuntimeClient.Object);

        // Act & Assert
        await Assert.ThrowsAsync<TimeoutException>(
            () => agent.WaitForAgentStatusAsync(
                AgentStatus.PREPARED,
                CancellationToken.None,
                1,
                1
            )
        );
    }

    private (Mock<AmazonBedrockAgentClient>, Mock<AmazonBedrockAgentRuntimeClient>) CreateMockClients()
    {
#pragma warning disable Moq1410 // Moq: Set MockBehavior to Strict
        Mock<AmazonBedrockAgentClient> mockClient = new();
        Mock<AmazonBedrockAgentRuntimeClient> mockRuntimeClient = new();
#pragma warning restore Moq1410 // Moq: Set MockBehavior to Strict

        // The agent reaches the PREPARED status after 1 attempts.
        mockClient.SetupSequence(x => x.GetAgentAsync(
            It.IsAny<GetAgentRequest>(),
            default)
        ).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.NOT_PREPARED,
            }
        }).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.PREPARED,
            }
        });

        return (mockClient, mockRuntimeClient);
    }
}