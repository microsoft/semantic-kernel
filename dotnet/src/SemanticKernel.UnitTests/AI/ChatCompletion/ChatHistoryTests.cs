// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
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
        var options = new JsonSerializerOptions();
        options.Converters.Add(new AuthorRoleConverter());
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
        var options = new JsonSerializerOptions();
        //options.Converters.Add(new AuthorRoleConverter());
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

    public class AuthorRoleConverter : JsonConverter<AuthorRole>
    {
        public override AuthorRole Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            // Assume the JSON is a string representing the label
            var label = reader.GetString();
            return new AuthorRole(label!);
        }

        public override void Write(Utf8JsonWriter writer, AuthorRole value, JsonSerializerOptions options)
        {
            // Write the label as a string
            writer.WriteStringValue(value.Label);
        }
    }
}
