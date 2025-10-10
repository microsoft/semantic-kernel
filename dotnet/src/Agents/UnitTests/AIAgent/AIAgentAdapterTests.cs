// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel.Agents;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AIAgent;

public sealed class AIAgentAdapterTests
{
    [Fact]
    public void Constructor_InitializesProperties()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act
        var adapter = new AIAgentAdapter(agentMock.Object, ThreadFactory, ThreadDeserializationFactory, ThreadSerializer);

        // Assert
        Assert.Equal(agentMock.Object, adapter.InnerAgent);
    }

    [Fact]
    public void Constructor_WithNullSemanticKernelAgent_ThrowsArgumentNullException()
    {
        // Arrange
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AIAgentAdapter(null!, ThreadFactory, ThreadDeserializationFactory, ThreadSerializer));
    }

    [Fact]
    public void Constructor_WithNullThreadFactory_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AIAgentAdapter(agentMock.Object, null!, ThreadDeserializationFactory, ThreadSerializer));
    }

    [Fact]
    public void Constructor_WithNullThreadDeserializationFactory_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AIAgentAdapter(agentMock.Object, ThreadFactory, null!, ThreadSerializer));
    }

    [Fact]
    public void Constructor_WithNullThreadSerializer_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AIAgentAdapter(agentMock.Object, ThreadFactory, ThreadDeserializationFactory, null!));
    }

    [Fact]
    public void DeserializeThread_ReturnsAIAgentThreadAdapter()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var expectedThread = Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => expectedThread;
        var adapter = new AIAgentAdapter(agentMock.Object, () => expectedThread, ThreadDeserializationFactory, ThreadSerializer);
        var json = JsonDocument.Parse("{}").RootElement;

        // Act
        var result = adapter.DeserializeThread(json);

        // Assert
        Assert.IsType<AIAgentThreadAdapter>(result);
    }

    [Fact]
    public void GetNewThread_ReturnsAIAgentThreadAdapter()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var expectedThread = Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;
        var adapter = new AIAgentAdapter(agentMock.Object, () => expectedThread, (e, o) => expectedThread, ThreadSerializer);

        // Act
        var result = adapter.GetNewThread();

        // Assert
        Assert.IsType<AIAgentThreadAdapter>(result);
        Assert.Equal(expectedThread, ((AIAgentThreadAdapter)result).InnerThread);
    }

    [Fact]
    public void DeserializeThread_CallsDeserializationFactory()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var expectedThread = Mock.Of<AgentThread>();
        var factoryCallCount = 0;

        AgentThread DeserializationFactory(JsonElement e, JsonSerializerOptions? o)
        {
            factoryCallCount++;
            return expectedThread;
        }

        var adapter = new AIAgentAdapter(agentMock.Object, () => expectedThread, DeserializationFactory, (t, o) => default);
        var json = JsonDocument.Parse("{}").RootElement;

        // Act
        var result = adapter.DeserializeThread(json);

        // Assert
        Assert.Equal(1, factoryCallCount);
        Assert.IsType<AIAgentThreadAdapter>(result);
    }

    [Fact]
    public void GetNewThread_CallsThreadFactory()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var expectedThread = Mock.Of<AgentThread>();
        var factoryCallCount = 0;

        AgentThread ThreadFactory()
        {
            factoryCallCount++;
            return expectedThread;
        }

        var adapter = new AIAgentAdapter(agentMock.Object, ThreadFactory, (e, o) => expectedThread, (t, o) => default);

        // Act
        var result = adapter.GetNewThread();

        // Assert
        Assert.Equal(1, factoryCallCount);
        Assert.IsType<AIAgentThreadAdapter>(result);
    }

    [Fact]
    public void InnerAgent_Property_ReturnsCorrectValue()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var adapter = new AIAgentAdapter(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        // Act
        var result = adapter.InnerAgent;

        // Assert
        Assert.Same(agentMock.Object, result);
    }
}
