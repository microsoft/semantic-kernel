// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;
using MAAI = Microsoft.Agents.AI;

namespace SemanticKernel.Agents.UnitTests.AIAgent;

public sealed class AIAgentAdapterTests
{
    [Fact]
    public void Constructor_Succeeds()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act
        var adapter = new AIAgentAdapter(agentMock.Object, ThreadFactory, ThreadDeserializationFactory, ThreadSerializer);

        // Assert
        Assert.IsType<AIAgentAdapter>(adapter);
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
    public async Task Run_CallsInnerAgentAsync()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var innerThread = threadMock.Object;
        var agentMock = new Mock<Agent>();
        agentMock.Setup(a => a.InvokeAsync(
            It.IsAny<List<ChatMessageContent>>(),
            It.IsAny<AgentThread>(),
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()))
            .Returns(GetAsyncEnumerable());
        var adapter = new AIAgentAdapter(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> GetAsyncEnumerable()
        {
            yield return new AgentResponseItem<ChatMessageContent>(new ChatMessageContent(AuthorRole.Assistant, "Final response"), innerThread);
        }

        var thread = new AIAgentThreadAdapter(innerThread, (t, o) => default);

        // Act
        var result = await adapter.RunAsync("Input text", thread);

        // Assert
        Assert.IsType<MAAI.AgentRunResponse>(result);
        Assert.Equal("Final response", result.Text);
        agentMock.Verify(a => a.InvokeAsync(
            It.Is<List<ChatMessageContent>>(x => x.First().Content == "Input text"),
            innerThread,
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task RunStreaming_CallsInnerAgentAsync()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var innerThread = threadMock.Object;
        var agentMock = new Mock<Agent>();
        agentMock.Setup(a => a.InvokeStreamingAsync(
            It.IsAny<List<ChatMessageContent>>(),
            It.IsAny<AgentThread>(),
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()))
            .Returns(GetAsyncEnumerable());
        var adapter = new AIAgentAdapter(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> GetAsyncEnumerable()
        {
            yield return new AgentResponseItem<StreamingChatMessageContent>(new StreamingChatMessageContent(AuthorRole.Assistant, "Final response"), innerThread);
        }

        var thread = new AIAgentThreadAdapter(innerThread, (t, o) => default);

        // Act
        var results = await adapter.RunStreamingAsync("Input text", thread).ToListAsync();

        // Assert
        Assert.IsType<MAAI.AgentRunResponseUpdate>(results.First());
        Assert.Equal("Final response", results.First().Text);
        agentMock.Verify(a => a.InvokeStreamingAsync(
            It.Is<List<ChatMessageContent>>(x => x.First().Content == "Input text"),
            innerThread,
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()), Times.Once);
    }
}
