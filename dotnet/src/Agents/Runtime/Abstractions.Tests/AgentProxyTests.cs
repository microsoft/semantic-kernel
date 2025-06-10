// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Abstractions.Tests;

[Trait("Category", "Unit")]
public class AgentProxyTests
{
    private readonly Mock<IAgentRuntime> mockRuntime;
    private readonly AgentId agentId;
    private readonly AgentProxy agentProxy;

    public AgentProxyTests()
    {
        this.mockRuntime = new Mock<IAgentRuntime>();
        this.agentId = new AgentId("testType", "testKey");
        this.agentProxy = new AgentProxy(this.agentId, this.mockRuntime.Object);
    }

    [Fact]
    public void IdMatchesAgentIdTest()
    {
        // Assert
        Assert.Equal(this.agentId, this.agentProxy.Id);
    }

    [Fact]
    public void MetadataShouldMatchAgentTest()
    {
        AgentMetadata expectedMetadata = new("testType", "testKey", "testDescription");
        this.mockRuntime.Setup(r => r.GetAgentMetadataAsync(this.agentId))
            .ReturnsAsync(expectedMetadata);

        Assert.Equal(expectedMetadata, this.agentProxy.Metadata);
    }

    [Fact]
    public async Task SendMessageResponseTest()
    {
        // Arrange
        object message = new { Content = "Hello" };
        AgentId sender = new("senderType", "senderKey");
        object response = new { Content = "Response" };

        this.mockRuntime.Setup(r => r.SendMessageAsync(message, this.agentId, sender, null, It.IsAny<CancellationToken>()))
            .ReturnsAsync(response);

        // Act
        object? result = await this.agentProxy.SendMessageAsync(message, sender);

        // Assert
        Assert.Equal(response, result);
    }

    [Fact]
    public async Task LoadStateTest()
    {
        // Arrange
        JsonElement state = JsonDocument.Parse("{\"key\":\"value\"}").RootElement;

        this.mockRuntime.Setup(r => r.LoadAgentStateAsync(this.agentId, state))
            .Returns(ValueTask.CompletedTask);

        // Act
        await this.agentProxy.LoadStateAsync(state);

        // Assert
        this.mockRuntime.Verify(r => r.LoadAgentStateAsync(this.agentId, state), Times.Once);
    }

    [Fact]
    public async Task SaveStateTest()
    {
        // Arrange
        JsonElement expectedState = JsonDocument.Parse("{\"key\":\"value\"}").RootElement;

        this.mockRuntime.Setup(r => r.SaveAgentStateAsync(this.agentId))
            .ReturnsAsync(expectedState);

        // Act
        JsonElement result = await this.agentProxy.SaveStateAsync();

        // Assert
        Assert.Equal(expectedState, result);
    }
}
