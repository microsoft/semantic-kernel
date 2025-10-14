// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Text.Json;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Moq;
using OpenAI.Assistants;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

public sealed class OpenAIAssistantAgentExtensionsTests
{
    private static readonly Assistant s_assistantDefinition = ModelReaderWriter.Read<Assistant>(BinaryData.FromString(
    """
    {
        "id": "asst_abc123",
        "object": "assistant",
        "created_at": 1698984975,
        "name": "TestAssistant",
        "description": "A test assistant",
        "model": "gpt-4",
        "instructions": "Test instructions",
        "tools": [],
        "metadata": {}
    }
    """))!;

    [Fact]
    public void AsAIAgent_WithValidOpenAIAssistantAgent_ReturnsAIAgentAdapter()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);

        // Act
        var result = assistantAgent.AsAIAgent();

        // Assert
        Assert.NotNull(result);
        Assert.IsType<AIAgentAdapter>(result);
    }

    [Fact]
    public void AsAIAgent_WithNullOpenAIAssistantAgent_ThrowsArgumentNullException()
    {
        // Arrange
        OpenAIAssistantAgent nullAgent = null!;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => nullAgent.AsAIAgent());
    }

    [Fact]
    public void AsAIAgent_CreatesWorkingThreadFactory()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);

        // Act
        var result = assistantAgent.AsAIAgent();
        var thread = result.GetNewThread();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<OpenAIAssistantAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithNullAgentId_CreatesNewThread()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = assistantAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<OpenAIAssistantAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithValidAgentId_CreatesThreadWithId()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);
        var threadId = "test-thread-id";
        var jsonElement = JsonSerializer.SerializeToElement(threadId);

        // Act
        var result = assistantAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<AIAgentThreadAdapter>(thread);
        var threadAdapter = (AIAgentThreadAdapter)thread;
        Assert.IsType<OpenAIAssistantAgentThread>(threadAdapter.InnerThread);
        Assert.Equal(threadId, threadAdapter.InnerThread.Id);
    }

    [Fact]
    public void AsAIAgent_ThreadSerializer_SerializesThreadId()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);
        var expectedThreadId = "test-thread-id";
        var assistantThread = new OpenAIAssistantAgentThread(clientMock.Object, expectedThreadId);
        var jsonElement = JsonSerializer.SerializeToElement(expectedThreadId);

        var result = assistantAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Act
        var serializedElement = thread.Serialize();

        // Assert
        Assert.Equal(JsonValueKind.String, serializedElement.ValueKind);
        Assert.Equal(expectedThreadId, serializedElement.GetString());
    }
}
