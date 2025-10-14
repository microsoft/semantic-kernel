// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Text.Json;
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AzureAI;

public sealed class AzureAIAgentExtensionsTests
{
    private static readonly JsonSerializerOptions s_jsonModelConvererOptions = new() { Converters = { new JsonModelConverter() } };
    private static readonly PersistentAgent s_agentMetadata = JsonSerializer.Deserialize<PersistentAgent>(
    """
    {
        "id": "1",
        "description": "A test agent",
        "name": "TestAgent"
    }
    """, s_jsonModelConvererOptions)!;

    [Fact]
    public void AsAIAgent_WithValidAzureAIAgent_ReturnsAIAgentAdapter()
    {
        // Arrange
        var clientMock = new Mock<Azure.AI.Agents.Persistent.PersistentAgentsClient>();
        var azureAIAgent = new AzureAIAgent(s_agentMetadata, clientMock.Object);

        // Act
        var result = azureAIAgent.AsAIAgent();

        // Assert
        Assert.NotNull(result);
        Assert.IsType<AIAgentAdapter>(result);
    }

    [Fact]
    public void AsAIAgent_WithNullAzureAIAgent_ThrowsArgumentNullException()
    {
        // Arrange
        AzureAIAgent nullAgent = null!;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => nullAgent.AsAIAgent());
    }

    [Fact]
    public void AsAIAgent_CreatesWorkingThreadFactory()
    {
        var clientMock = new Mock<Azure.AI.Agents.Persistent.PersistentAgentsClient>();
        var azureAIAgent = new AzureAIAgent(s_agentMetadata, clientMock.Object);

        // Act
        var result = azureAIAgent.AsAIAgent();
        var thread = result.GetNewThread();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<AzureAIAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithNullAgentId_CreatesNewThread()
    {
        // Arrange
        var clientMock = new Mock<Azure.AI.Agents.Persistent.PersistentAgentsClient>();
        var azureAIAgent = new AzureAIAgent(s_agentMetadata, clientMock.Object);
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = azureAIAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<AzureAIAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithValidAgentId_CreatesThreadWithId()
    {
        // Arrange
        var clientMock = new Mock<Azure.AI.Agents.Persistent.PersistentAgentsClient>();
        var azureAIAgent = new AzureAIAgent(s_agentMetadata, clientMock.Object);

        var threadId = "test-thread-id";
        var jsonElement = JsonSerializer.SerializeToElement(threadId);

        // Act
        var result = azureAIAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<AzureAIAgentThread>(threadAdapter.InnerThread);
        Assert.Equal(threadId, threadAdapter.InnerThread.Id);
    }

    [Fact]
    public void AsAIAgent_ThreadSerializer_SerializesThreadId()
    {
        // Arrange
        var clientMock = new Mock<Azure.AI.Agents.Persistent.PersistentAgentsClient>();
        var azureAIAgent = new AzureAIAgent(s_agentMetadata, clientMock.Object);

        var expectedThreadId = "test-thread-id";
        var azureAIThread = new AzureAIAgentThread(clientMock.Object, expectedThreadId);
        var jsonElement = JsonSerializer.SerializeToElement(expectedThreadId);

        var result = azureAIAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Act
        var serializedElement = thread.Serialize();

        // Assert
        Assert.Equal(JsonValueKind.String, serializedElement.ValueKind);
        Assert.Equal(expectedThreadId, serializedElement.GetString());
    }
}
