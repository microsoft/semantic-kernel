// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Text.Json;
using System.Threading.Tasks;
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
        var responseClient = new ResponsesClient(new ApiKeyCredential("apikey"));
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
    public async Task AsAIAgent_CreatesWorkingThreadFactoryStoreTrue()
    {
        // Arrange
        var responseClient = new ResponsesClient(new ApiKeyCredential("apikey"));
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = true
        };

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = await result.CreateSessionAsync();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<OpenAIResponseAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public async Task AsAIAgent_CreatesWorkingThreadFactoryStoreFalse()
    {
        // Arrange
        var responseClient = new ResponsesClient(new ApiKeyCredential("apikey"));
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = false
        };

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = await result.CreateSessionAsync();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<ChatHistoryAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public async Task AsAIAgent_ThreadDeserializationFactory_WithNullAgentId_CreatesNewThread()
    {
        // Arrange
        var responseClient = new ResponsesClient(new ApiKeyCredential("apikey"));
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = true
        };
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<OpenAIResponseAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public async Task AsAIAgent_ThreadDeserializationFactory_WithValidAgentId_CreatesThreadWithId()
    {
        // Arrange
        var responseClient = new ResponsesClient(new ApiKeyCredential("apikey"));
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = true
        };
        var threadId = "test-agent-id";
        var jsonElement = JsonSerializer.SerializeToElement(threadId);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<OpenAIResponseAgentThread>(threadAdapter.InnerThread);
        Assert.Equal(threadId, threadAdapter.InnerThread.Id);
    }

    [Fact]
    public async Task AsAIAgent_ThreadSerializer_SerializesThreadId()
    {
        // Arrange
        var responseClient = new ResponsesClient(new ApiKeyCredential("apikey"));
        var responseAgent = new OpenAIResponseAgent(responseClient)
        {
            StoreEnabled = true
        };
        var expectedThreadId = "test-thread-id";
        var responseThread = new OpenAIResponseAgentThread(responseClient, expectedThreadId);
        var jsonElement = JsonSerializer.SerializeToElement(expectedThreadId);

        var result = responseAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Act
        var serializedElement = await result.SerializeSessionAsync(thread);

        // Assert
        Assert.Equal(JsonValueKind.String, serializedElement.ValueKind);
        Assert.Equal(expectedThreadId, serializedElement.GetString());
    }

    [Fact]
    public async Task AsAIAgent_ThreadDeserializationFactory_WithNullJson_CreatesThreadWithEmptyChatHistory()
    {
        var responseClient = new ResponsesClient(new ApiKeyCredential("apikey"));
        var responseAgent = new OpenAIResponseAgent(responseClient);
        var jsonElement = JsonSerializer.SerializeToElement((string?)null);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        var chatHistoryAgentThread = Assert.IsType<ChatHistoryAgentThread>(threadAdapter.InnerThread);
        Assert.Empty(chatHistoryAgentThread.ChatHistory);
    }

    [Fact]
    public async Task AsAIAgent_ThreadDeserializationFactory_WithChatHistory_CreatesThreadWithChatHistory()
    {
        var responseClient = new ResponsesClient(new ApiKeyCredential("apikey"));
        var responseAgent = new OpenAIResponseAgent(responseClient);
        var expectedChatHistory = new ChatHistory("mock message", AuthorRole.User);
        var jsonElement = JsonSerializer.SerializeToElement(expectedChatHistory);

        // Act
        var result = responseAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        var chatHistoryAgentThread = Assert.IsType<ChatHistoryAgentThread>(threadAdapter.InnerThread);
        Assert.Single(chatHistoryAgentThread.ChatHistory);
        var firstMessage = chatHistoryAgentThread.ChatHistory[0];
        Assert.Equal(AuthorRole.User, firstMessage.Role);
        Assert.Equal("mock message", firstMessage.Content);
    }

    [Fact]
    public async Task AsAIAgent_ThreadSerializer_SerializesChatHistory()
    {
        // Arrange
        var responseClient = new ResponsesClient(new ApiKeyCredential("apikey"));
        var responseAgent = new OpenAIResponseAgent(responseClient);
        var expectedChatHistory = new ChatHistory("mock message", AuthorRole.User);
        var jsonElement = JsonSerializer.SerializeToElement(expectedChatHistory);

        var result = responseAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Act
        var serializedElement = await result.SerializeSessionAsync(thread);

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
