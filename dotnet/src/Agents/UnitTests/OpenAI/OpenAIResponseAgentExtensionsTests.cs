// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.Responses;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

public sealed class OpenAIResponseAgentExtensionsTests
{
    [Fact]
    public void AsAIAgent_WithValidOpenAIResponseAgent_ReturnsAIAgentAdapter()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);

        // Act
        var result = responseAgent.AsAIAgent();

        // Assert
        Assert.NotNull(result);
        Assert.IsType<AIAgentAdapter>(result);
    }

    [Fact]
    public void AsAIAgent_WithNullOpenAIResponseAgent_ThrowsArgumentNullException()
    {
        // Arrange
        OpenAIResponseAgent nullAgent = null!;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => nullAgent.AsAIAgent());
    }

    [Fact]
    public void AsAIAgent_ReturnsAdapterWithCorrectInnerAgent()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);

        // Act
        var result = responseAgent.AsAIAgent();

        // Assert
        var adapter = Assert.IsType<AIAgentAdapter>(result);
        Assert.Same(responseAgent, adapter.InnerAgent);
    }

    [Fact]
    public void AsAIAgent_CreatesWorkingThreadFactory()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = result.GetNewThread();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<OpenAIResponseAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithNullAgentId_CreatesNewThread()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<OpenAIResponseAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithValidAgentId_CreatesThreadWithId()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);
        var threadId = "test-agent-id";
        var jsonElement = JsonSerializer.SerializeToElement(threadId);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<OpenAIResponseAgentThread>(threadAdapter.InnerThread);
        Assert.Equal(threadId, threadAdapter.InnerThread.Id);
    }

    [Fact]
    public void AsAIAgent_ThreadSerializer_SerializesThreadId()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);
        var expectedThreadId = "test-thread-id";
        var responseThread = new OpenAIResponseAgentThread(responseClient, expectedThreadId);
        var jsonElement = JsonSerializer.SerializeToElement(expectedThreadId);

        var result = responseAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Act
        var serializedElement = thread.Serialize();

        // Assert
        Assert.Equal(JsonValueKind.String, serializedElement.ValueKind);
        Assert.Equal(expectedThreadId, serializedElement.GetString());
    }
}
