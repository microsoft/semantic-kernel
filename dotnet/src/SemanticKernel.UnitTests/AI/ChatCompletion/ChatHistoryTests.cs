// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

/// <summary>
/// Unit tests of <see cref="ChatHistory"/>.
/// </summary>
public class ChatHistoryTests
{
    [Fact]
    public void ItCanBeSerialized()
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
    public void ItCanBeDeserialized()
    {
        // Arrange
        var options = new JsonSerializerOptions();
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");
        chatHistory.AddMessage(AuthorRole.Assistant, "Hi");
        var chatHistoryJson = JsonSerializer.Serialize(chatHistory, options);

        // Act
        var chatHistoryDeserialized = JsonSerializer.Deserialize<ChatHistory>(chatHistoryJson, options);

        // Assert
        Assert.NotNull(chatHistoryDeserialized);
        Assert.Equal(chatHistory.Count, chatHistoryDeserialized.Count);
        for (var i = 0; i < chatHistory.Count; i++)
        {
            Assert.Equal(chatHistory[i].Role.Label, chatHistoryDeserialized[i].Role.Label);
            Assert.Equal(chatHistory[i].Content, chatHistoryDeserialized[i].Content);
        }
    }
}
