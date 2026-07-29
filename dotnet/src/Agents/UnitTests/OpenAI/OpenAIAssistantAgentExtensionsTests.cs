// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Text.Json;
using System.Threading.Tasks;
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
    public void AsAIAgent_WithValidOpenAIAssistantAgent_ReturnsSemanticKernelAIAgent()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);

        // Act
        var result = assistantAgent.AsAIAgent();

        // Assert
        Assert.NotNull(result);
        Assert.IsType<SemanticKernelAIAgent>(result);
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
    public async Task AsAIAgent_CreatesWorkingThreadFactory()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);

        // Act
        var result = assistantAgent.AsAIAgent();
        var thread = await result.CreateSessionAsync();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<OpenAIAssistantAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public async Task AsAIAgent_ThreadDeserializationFactory_WithNullAgentId_CreatesNewThread()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = assistantAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<OpenAIAssistantAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public async Task AsAIAgent_ThreadDeserializationFactory_WithValidAgentId_CreatesThreadWithId()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);
        var threadId = "test-thread-id";
        var jsonElement = JsonSerializer.SerializeToElement(threadId);

        // Act
        var result = assistantAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<OpenAIAssistantAgentThread>(threadAdapter.InnerThread);
        Assert.Equal(threadId, threadAdapter.InnerThread.Id);
    }

    [Fact]
    public async Task AsAIAgent_ThreadSerializer_SerializesThreadId()
    {
        // Arrange
        var clientMock = new Mock<AssistantClient>();
        var assistantAgent = new OpenAIAssistantAgent(s_assistantDefinition, clientMock.Object);
        var expectedThreadId = "test-thread-id";
        var assistantThread = new OpenAIAssistantAgentThread(clientMock.Object, expectedThreadId);
        var jsonElement = JsonSerializer.SerializeToElement(expectedThreadId);

        var result = assistantAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Act
        var serializedElement = await result.SerializeSessionAsync(thread);

        // Assert
        Assert.Equal(JsonValueKind.String, serializedElement.ValueKind);
        Assert.Equal(expectedThreadId, serializedElement.GetString());
    }
}
