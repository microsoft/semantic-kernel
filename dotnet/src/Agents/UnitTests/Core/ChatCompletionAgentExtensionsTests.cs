// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;
namespace SemanticKernel.Agents.UnitTests.Core;

public sealed class ChatCompletionAgentExtensionsTests
{
    [Fact]
    public void AsAIAgent_WithValidChatCompletionAgent_ReturnsSemanticKernelAIAgent()
    {
        // Arrange
        var chatCompletionAgent = new ChatCompletionAgent()
        {
            Name = "TestAgent",
            Instructions = "Test instructions"
        };

        // Act
        var result = chatCompletionAgent.AsAIAgent();

        // Assert
        Assert.NotNull(result);
        Assert.IsType<SemanticKernelAIAgent>(result);
    }

    [Fact]
    public void AsAIAgent_WithNullChatCompletionAgent_ThrowsArgumentNullException()
    {
        // Arrange
        ChatCompletionAgent nullAgent = null!;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => nullAgent.AsAIAgent());
    }

    [Fact]
    public async Task AsAIAgent_CreatesWorkingThreadFactory()
    {
        // Arrange
        var chatCompletionAgent = new ChatCompletionAgent()
        {
            Name = "TestAgent",
            Instructions = "Test instructions"
        };

        // Act
        var result = chatCompletionAgent.AsAIAgent();
        var thread = await result.CreateSessionAsync();

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<ChatHistoryAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public async Task AsAIAgent_ThreadDeserializationFactory_WithNullChatHistory_CreatesNewThread()
    {
        // Arrange
        var chatCompletionAgent = new ChatCompletionAgent()
        {
            Name = "TestAgent",
            Instructions = "Test instructions"
        };
        var jsonElement = JsonSerializer.SerializeToElement((ChatHistory?)null);

        // Act
        var result = chatCompletionAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<ChatHistoryAgentThread>(threadAdapter.InnerThread);
    }

    [Fact]
    public async Task AsAIAgent_ThreadDeserializationFactory_WithValidChatHistory_CreatesThreadWithHistory()
    {
        // Arrange
        var chatCompletionAgent = new ChatCompletionAgent()
        {
            Name = "TestAgent",
            Instructions = "Test instructions"
        };

        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("System message");
        chatHistory.AddUserMessage("User message");
        var jsonElement = JsonSerializer.SerializeToElement(chatHistory);

        // Act
        var result = chatCompletionAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Assert
        Assert.NotNull(thread);
        Assert.IsType<SemanticKernelAIAgentSession>(thread);
        var threadAdapter = (SemanticKernelAIAgentSession)thread;
        Assert.IsType<ChatHistoryAgentThread>(threadAdapter.InnerThread);
        var chatHistoryThread = (ChatHistoryAgentThread)threadAdapter.InnerThread;
        Assert.Equal(2, chatHistoryThread.ChatHistory.Count);
    }

    [Fact]
    public async Task AsAIAgent_ThreadSerializer_SerializesChatHistory()
    {
        // Arrange
        var chatCompletionAgent = new ChatCompletionAgent()
        {
            Name = "TestAgent",
            Instructions = "Test instructions"
        };

        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("System message");
        chatHistory.AddUserMessage("User message");
        var chatHistoryThread = new ChatHistoryAgentThread(chatHistory);
        var jsonElement = JsonSerializer.SerializeToElement(chatHistory);

        var result = chatCompletionAgent.AsAIAgent();
        var thread = await result.DeserializeSessionAsync(jsonElement);

        // Act
        var serializedElement = await result.SerializeSessionAsync(thread);

        // Assert
        Assert.Equal(JsonValueKind.Array, serializedElement.ValueKind);
        var deserializedChatHistory = JsonSerializer.Deserialize<ChatHistory>(serializedElement.GetRawText());
        Assert.NotNull(deserializedChatHistory);
        Assert.Equal(2, deserializedChatHistory.Count);
    }
}
