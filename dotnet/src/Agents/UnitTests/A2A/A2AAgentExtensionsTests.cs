// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json;
using A2A;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.A2A;

public sealed class A2AAgentExtensionsTests
{
    [Fact]
    public void AsAIAgent_WithValidA2AAgent_ReturnsAIAgentAdapter()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var a2aClient = new A2AClient(new Uri("http://testservice", UriKind.Absolute), httpClient);
        var agentCard = new AgentCard();
        var a2aAgent = new A2AAgent(a2aClient, agentCard);

        // Act
        var result = a2aAgent.AsAIAgent();

        // Assert
        Assert.NotNull(result);
        Assert.IsType<AIAgentAdapter>(result);
    }

    [Fact]
    public void AsAIAgent_WithNullA2AAgent_ThrowsArgumentNullException()
    {
        // Arrange
        A2AAgent nullAgent = null!;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => nullAgent.AsAIAgent());
    }

    [Fact]
    public void AsAIAgent_CreatesWorkingThreadFactory()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var a2aClient = new A2AClient(new Uri("http://testservice", UriKind.Absolute), httpClient);
        var agentCard = new AgentCard();
        var a2aAgent = new A2AAgent(a2aClient, agentCard);

        // Act
        var result = a2aAgent.AsAIAgent();
        var thread = result.GetNewThread();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<A2AAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithNullAgentId_CreatesNewThread()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var a2aClient = new A2AClient(new Uri("http://testservice", UriKind.Absolute), httpClient);
        var agentCard = new AgentCard();
        var a2aAgent = new A2AAgent(a2aClient, agentCard);
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = a2aAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<A2AAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithValidAgentId_CreatesThreadWithId()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var a2aClient = new A2AClient(new Uri("http://testservice", UriKind.Absolute), httpClient);
        var agentCard = new AgentCard();
        var a2aAgent = new A2AAgent(a2aClient, agentCard);
        var threadId = "test-agent-id";
        var jsonElement = JsonSerializer.SerializeToElement(threadId);

        // Act
        var result = a2aAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<A2AAgentThread>(threadAdapter.InnerThread);
        Assert.Equal(threadId, threadAdapter.InnerThread.Id);
    }

    [Fact]
    public void AsAIAgent_ThreadSerializer_SerializesThreadId()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var a2aClient = new A2AClient(new Uri("http://testservice", UriKind.Absolute), httpClient);
        var agentCard = new AgentCard();
        var a2aAgent = new A2AAgent(a2aClient, agentCard);
        var expectedThreadId = "test-thread-id";
        var a2aThread = new A2AAgentThread(a2aClient, expectedThreadId);
        var jsonElement = JsonSerializer.SerializeToElement(expectedThreadId);

        var result = a2aAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Act
        var serializedElement = thread.Serialize();

        // Assert
        Assert.Equal(JsonValueKind.String, serializedElement.ValueKind);
        Assert.Equal(expectedThreadId, serializedElement.GetString());
    }
}
