// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

public sealed class OpenAIResponseAgentExtensionsTests
{
    [Fact]
    public void AsAIAgent_WithValidOpenAIResponseAgent_ReturnsSemanticKernelAIAgent()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);

        // Act
        var result = responseAgent.AsAIAgent();

        // Assert
        Assert.NotNull(result);
        Assert.IsType<SemanticKernelAIAgent>(result);
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
    public void AsAIAgent_CreatesWorkingThreadFactoryStoreTrue()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = true
        };

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = result.GetNewThread();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentThread>(thread);
        var threadAdapter = (SemanticKernelAIAgentThread)thread;
        Assert.IsType<OpenAIResponseAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_CreatesWorkingThreadFactoryStoreFalse()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = false
        };

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = result.GetNewThread();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentThread>(thread);
        var threadAdapter = (SemanticKernelAIAgentThread)thread;
        Assert.IsType<ChatHistoryAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithNullAgentId_CreatesNewThread()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = true
        };
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentThread>(thread);
        var threadAdapter = (SemanticKernelAIAgentThread)thread;
        Assert.IsType<OpenAIResponseAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithValidAgentId_CreatesThreadWithId()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = true
        };
        var threadId = "test-agent-id";
        var jsonElement = JsonSerializer.SerializeToElement(threadId);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentThread>(thread);
        var threadAdapter = (SemanticKernelAIAgentThread)thread;
        Assert.IsType<OpenAIResponseAgentThread>(threadAdapter.InnerThread);
        Assert.Equal(threadId, threadAdapter.InnerThread.Id);
    }

    [Fact]
    public void AsAIAgent_ThreadSerializer_SerializesThreadId()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = true
        };
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

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithNullJson_CreatesThreadWithEmptyChatHistory()
    {
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentThread>(thread);
        var threadAdapter = (SemanticKernelAIAgentThread)thread;
        var chatHistoryAgentThread = Assert.IsType<ChatHistoryAgentThread>(threadAdapter.InnerThread);
        Assert.Empty(chatHistoryAgentThread.ChatHistory);
    }

    [Fact]
    public void AsAIAgent_ThreadDeserializationFactory_WithChatHistory_CreatesThreadWithChatHistory()
    {
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);
        var expectedChatHistory = new ChatHistory("mock message", AuthorRole.User);
        var jsonElement = JsonSerializer.SerializeToElement(expectedChatHistory);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentThread>(thread);
        var threadAdapter = (SemanticKernelAIAgentThread)thread;
        var chatHistoryAgentThread = Assert.IsType<ChatHistoryAgentThread>(threadAdapter.InnerThread);
        Assert.Single(chatHistoryAgentThread.ChatHistory);
        var firstMessage = chatHistoryAgentThread.ChatHistory[0];
        Assert.Equal(AuthorRole.User, firstMessage.Role);
        Assert.Equal("mock message", firstMessage.Content);
    }

    [Fact]
    public void AsAIAgent_ThreadSerializer_SerializesChatHistory()
    {
        // Arrange
        var responseClient = new OpenAIResponseClient("model", "apikey");
        var responseAgent = new OpenAIResponseAgent(responseClient);
        var expectedChatHistory = new ChatHistory("mock message", AuthorRole.User);
        var jsonElement = JsonSerializer.SerializeToElement(expectedChatHistory);

        var result = responseAgent.AsAIAgent();
        var thread = result.DeserializeThread(jsonElement);

        // Act
        var serializedElement = thread.Serialize();

        // Assert
        Assert.Equal(JsonValueKind.Array, serializedElement.ValueKind);
        Assert.Equal(1, serializedElement.GetArrayLength());

        var firstMessage = serializedElement[0];
        Assert.True(firstMessage.TryGetProperty("Role", out var roleProp));
        Assert.Equal("user", roleProp.GetProperty("Label").GetString());

        Assert.True(firstMessage.TryGetProperty("Items", out var itemsProp));
        Assert.Equal(1, itemsProp.GetArrayLength());

        var firstItem = itemsProp[0];
        Assert.Equal("TextContent", firstItem.GetProperty("$type").GetString());
        Assert.Equal("mock message", firstItem.GetProperty("Text").GetString());
    }
}
