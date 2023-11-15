// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.AI.ChatCompletion;
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
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");
        chatHistory.AddMessage(AuthorRole.Assistant, "Hi");

        // Act
        var chatHistoryJson = JsonSerializer.Serialize(chatHistory);

        // Assert
        Assert.NotNull(chatHistoryJson);
        Assert.Equal("[{\"Role\":{\"Label\":\"user\"},\"Content\":\"Hello\",\"AdditionalProperties\":null},{\"Role\":{\"Label\":\"assistant\"},\"Content\":\"Hi\",\"AdditionalProperties\":null}]", chatHistoryJson);
    }

    [Fact]
    public void ItCanBeDeserialised()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");
        chatHistory.AddMessage(AuthorRole.Assistant, "Hi");
        var chatHistoryJson = JsonSerializer.Serialize(chatHistory);

        // Act
        var chatHistoryDeserialised = JsonSerializer.Deserialize<ChatHistory>(chatHistoryJson);

        // Assert
        Assert.NotNull(chatHistoryDeserialised);
        //Assert.Same(chatHistory, chatHistoryDeserialised);
    }
}
