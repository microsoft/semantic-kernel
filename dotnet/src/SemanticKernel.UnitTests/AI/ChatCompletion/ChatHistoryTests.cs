// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

/// <summary>
/// Unit tests of <see cref="ChatHistory"/>.
/// </summary>
public class ChatHistoryTests
{
    [Fact]
    public void ItCanBeSerialised()
    {
        // Arrange
        var options = new JsonSerializerOptions();
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");
        chatHistory.AddMessage(AuthorRole.Assistant, "Hi");

        // Act
        var chatHistoryJson = JsonSerializer.Serialize(chatHistory);

        // Assert
        Assert.NotNull(chatHistoryJson);
        Assert.Equal("[{\"Role\":{\"Label\":\"user\"},\"Content\":\"Hello\",\"Items\":null,\"ModelId\":null,\"Metadata\":null},{\"Role\":{\"Label\":\"assistant\"},\"Content\":\"Hi\",\"Items\":null,\"ModelId\":null,\"Metadata\":null}]", chatHistoryJson);
    }

    [Fact]
    public void ItCanBeDeserialised()
    {
        // Arrange
        var options = new JsonSerializerOptions();
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");
        chatHistory.AddMessage(AuthorRole.Assistant, "Hi");
        var chatHistoryJson = JsonSerializer.Serialize(chatHistory, options);

        // Act
        var chatHistoryDeserialised = JsonSerializer.Deserialize<ChatHistory>(chatHistoryJson, options);

        // Assert
        Assert.NotNull(chatHistoryDeserialised);
        Assert.Equal(chatHistory.Count, chatHistoryDeserialised.Count);
        for (var i = 0; i < chatHistory.Count; i++)
        {
            Assert.Equal(chatHistory[i].Role.Label, chatHistoryDeserialised[i].Role.Label);
            Assert.Equal(chatHistory[i].Content, chatHistoryDeserialised[i].Content);
        }
    }

    [Fact]
    public async Task ItCanAddMessageFromStreamingChatContentsAsync()
    {
        var chatHistoryStreamingContents = new List<StreamingChatMessageContent>
        {
            new(AuthorRole.User, "Hello "),
            new(null, ", "),
            new(null, "I "),
            new(null, "am "),
            new(null, "a "),
            new(null, "test "),
        }.ToAsyncEnumerable();

        var chatHistory = new ChatHistory();
        var finalContent = "Hello , I am a test ";
        string processedContent = string.Empty;
        await foreach (var chatMessageChunk in chatHistory.AddStreamingMessageAsync<StreamingChatMessageContent>(chatHistoryStreamingContents))
        {
            processedContent += chatMessageChunk.Content;
        }

        Assert.Single(chatHistory);
        Assert.Equal(finalContent, processedContent);
        Assert.Equal(finalContent, chatHistory[0].Content);
        Assert.Equal(AuthorRole.User, chatHistory[0].Role);
    }
}
