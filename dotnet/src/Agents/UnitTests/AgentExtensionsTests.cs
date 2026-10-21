// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Moq;
using Xunit;
namespace SemanticKernel.Agents.UnitTests;

public sealed class AgentExtensionsTests
{
    [Fact]
    public void AsAIAgent_WithValidParameters_ReturnsSemanticKernelAIAgent()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act
        var result = agentMock.Object.AsAIAgent(ThreadFactory, ThreadDeserializationFactory, ThreadSerializer);

        // Assert
        Assert.NotNull(result);
        Assert.IsType<SemanticKernelAIAgent>(result);
    }

    [Fact]
    public void AsAIAgent_WithNullSemanticKernelAgent_ThrowsArgumentNullException()
    {
        // Arrange
        Agent nullAgent = null!;
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => nullAgent.AsAIAgent(ThreadFactory, ThreadDeserializationFactory, ThreadSerializer));
    }

    [Fact]
    public void AsAIAgent_WithNullThreadFactory_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => agentMock.Object.AsAIAgent(null!, ThreadDeserializationFactory, ThreadSerializer));
    }

    [Fact]
    public void AsAIAgent_WithNullThreadDeserializationFactory_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => agentMock.Object.AsAIAgent(ThreadFactory, null!, ThreadSerializer));
    }

    [Fact]
    public void AsAIAgent_WithNullThreadSerializer_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => agentMock.Object.AsAIAgent(ThreadFactory, ThreadDeserializationFactory, null!));
    }

    [Fact]
    public async Task AsAIAgent_WithValidFactories_CreatesWorkingAdapter()
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

        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => expectedThread;
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act
        var result = agentMock.Object.AsAIAgent(ThreadFactory, ThreadDeserializationFactory, ThreadSerializer);
        var thread = await result.CreateSessionAsync();

        // Assert
        Assert.NotNull(thread);
        Assert.Equal(1, factoryCallCount);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        Assert.Same(expectedThread, ((SemanticKernelAIAgentSession)thread).InnerThread);
    }

    [Fact]
    public async Task AsAIAgent_WithDeserializationFactory_CreatesWorkingAdapter()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var expectedThread = Mock.Of<AgentThread>();
        var deserializationCallCount = 0;

        AgentThread ThreadFactory() => Mock.Of<AgentThread>();

        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o)
        {
            deserializationCallCount++;
            return expectedThread;
        }

        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act
        var result = agentMock.Object.AsAIAgent(ThreadFactory, ThreadDeserializationFactory, ThreadSerializer);
        var json = JsonElement.Parse("{}");
        var thread = await result.DeserializeSessionAsync(json);

        // Assert
        Assert.NotNull(thread);
        Assert.Equal(1, deserializationCallCount);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        Assert.Same(expectedThread, ((SemanticKernelAIAgentSession)thread).InnerThread);
    }
}
