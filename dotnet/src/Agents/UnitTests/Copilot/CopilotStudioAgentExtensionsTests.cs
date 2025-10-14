// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.Agents.CopilotStudio.Client;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Copilot;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Copilot;

public sealed class CopilotStudioAgentExtensionsTests
{
    [Fact]
    public void AsAIAgent_WithValidCopilotStudioAgent_ReturnsAIAgentAdapter()
    {
        // Arrange
        var clientMock = new Mock<CopilotClient>(null, null, null, null);
        var copilotStudioAgent = new CopilotStudioAgent(clientMock.Object);

        // Act
        var result = copilotStudioAgent.AsAIAgent();

        // Assert
        Assert.NotNull(result);
        Assert.IsType<AIAgentAdapter>(result);
    }

    [Fact]
    public void AsAIAgent_WithNullCopilotStudioAgent_ThrowsArgumentNullException()
    {
        // Arrange
        CopilotStudioAgent nullAgent = null!;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => nullAgent.AsAIAgent());
    }

    [Fact]
    public void AsAIAgent_CreatesWorkingThreadFactory()
    {
        // Arrange
        var clientMock = new Mock<CopilotClient>(null, null, null, null);
        var copilotStudioAgent = new CopilotStudioAgent(clientMock.Object);

        // Act
        var result = copilotStudioAgent.AsAIAgent();
        var thread = result.GetNewThread();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<CopilotStudioAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithNullAgentId_CreatesNewThread()
    {
        // Arrange
        var clientMock = new Mock<CopilotClient>(null, null, null, null);
        var copilotStudioAgent = new CopilotStudioAgent(clientMock.Object);
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = copilotStudioAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<CopilotStudioAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithValidAgentId_CreatesThreadWithId()
    {
        // Arrange
        var clientMock = new Mock<CopilotClient>(null, null, null, null);
        var copilotStudioAgent = new CopilotStudioAgent(clientMock.Object);
        var agentId = "test-agent-id";
        var jsonElement = JsonSerializer.SerializeToElement(agentId);

        // Act
        var result = copilotStudioAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<CopilotStudioAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadSerializer_SerializesThreadId()
    {
        // Arrange
        var clientMock = new Mock<CopilotClient>(null, null, null, null);
        var copilotStudioAgent = new CopilotStudioAgent(clientMock.Object);
        var expectedThreadId = "test-thread-id";
        var copilotStudioThread = new CopilotStudioAgentThread(clientMock.Object, expectedThreadId);
        var jsonElement = JsonSerializer.SerializeToElement(expectedThreadId);

        var result = copilotStudioAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Act
        var serializedElement = thread.Serialize();

        // Assert
        Assert.Equal(JsonValueKind.String, serializedElement.ValueKind);
        Assert.Equal(expectedThreadId, serializedElement.GetString());
    }
}
