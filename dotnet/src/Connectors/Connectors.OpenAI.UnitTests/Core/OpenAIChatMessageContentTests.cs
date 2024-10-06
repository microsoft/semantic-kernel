// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using System.Collections;
using System.Collections.Generic;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using System.Collections;
using System.Collections.Generic;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
using System.Collections;
using System.Collections.Generic;
=======
>>>>>>> Stashed changes
using System;
using System.Collections;
using System.Collections.Generic;
using System.Text.Json;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

/// <summary>
/// Unit tests for <see cref="OpenAIChatMessageContent"/> class.
/// </summary>
public sealed class OpenAIChatMessageContentTests
{
    [Fact]
    public void ConstructorsWorkCorrectly()
    {
        // Arrange
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        List<ChatToolCall> toolCalls = [ChatToolCall.CreateFunctionToolCall("id", "name", "args")];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        List<ChatToolCall> toolCalls = [ChatToolCall.CreateFunctionToolCall("id", "name", "args")];
=======
        List<ChatToolCall> toolCalls = [ChatToolCall.CreateFunctionToolCall("id", "name", BinaryData.FromString("args"))];
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        List<ChatToolCall> toolCalls = [ChatToolCall.CreateFunctionToolCall("id", "name", BinaryData.FromString("args"))];
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

        // Act
        var content1 = new OpenAIChatMessageContent(ChatMessageRole.User, "content1", "model-id1", toolCalls) { AuthorName = "Fred" };
        var content2 = new OpenAIChatMessageContent(AuthorRole.User, "content2", "model-id2", toolCalls);

        // Assert
        this.AssertChatMessageContent(AuthorRole.User, "content1", "model-id1", toolCalls, content1, "Fred");
        this.AssertChatMessageContent(AuthorRole.User, "content2", "model-id2", toolCalls, content2);
    }

    [Fact]
    public void GetOpenAIFunctionToolCallsReturnsCorrectList()
    {
        // Arrange
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        List<ChatToolCall> toolCalls = [
            ChatToolCall.CreateFunctionToolCall("id1", "name", string.Empty),
            ChatToolCall.CreateFunctionToolCall("id2", "name", string.Empty)];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        List<ChatToolCall> toolCalls = [
            ChatToolCall.CreateFunctionToolCall("id1", "name", string.Empty),
            ChatToolCall.CreateFunctionToolCall("id2", "name", string.Empty)];
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());

        List<ChatToolCall> toolCalls = [
            ChatToolCall.CreateFunctionToolCall("id1", "name", BinaryData.FromString(args)),
            ChatToolCall.CreateFunctionToolCall("id2", "name", BinaryData.FromString(args))];
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

        var content1 = new OpenAIChatMessageContent(AuthorRole.User, "content", "model-id", toolCalls);
        var content2 = new OpenAIChatMessageContent(AuthorRole.User, "content", "model-id", []);

        // Act
        var actualToolCalls1 = content1.GetOpenAIFunctionToolCalls();
        var actualToolCalls2 = content2.GetOpenAIFunctionToolCalls();

        // Assert
        Assert.Equal(2, actualToolCalls1.Count);
        Assert.Equal("id1", actualToolCalls1[0].Id);
        Assert.Equal("id2", actualToolCalls1[1].Id);

        Assert.Empty(actualToolCalls2);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void MetadataIsInitializedCorrectly(bool readOnlyMetadata)
    {
        // Arrange
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());

>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        IReadOnlyDictionary<string, object?> metadata = readOnlyMetadata ?
            new CustomReadOnlyDictionary<string, object?>(new Dictionary<string, object?> { { "key", "value" } }) :
            new Dictionary<string, object?> { { "key", "value" } };

        List<ChatToolCall> toolCalls = [
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            ChatToolCall.CreateFunctionToolCall("id1", "name", string.Empty),
            ChatToolCall.CreateFunctionToolCall("id2", "name", string.Empty)];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            ChatToolCall.CreateFunctionToolCall("id1", "name", string.Empty),
            ChatToolCall.CreateFunctionToolCall("id2", "name", string.Empty)];
=======
            ChatToolCall.CreateFunctionToolCall("id1", "name", BinaryData.FromString(args)),
            ChatToolCall.CreateFunctionToolCall("id2", "name", BinaryData.FromString(args))];
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            ChatToolCall.CreateFunctionToolCall("id1", "name", BinaryData.FromString(args)),
            ChatToolCall.CreateFunctionToolCall("id2", "name", BinaryData.FromString(args))];
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

        // Act
        var content1 = new OpenAIChatMessageContent(AuthorRole.User, "content1", "model-id1", [], metadata);
        var content2 = new OpenAIChatMessageContent(AuthorRole.User, "content2", "model-id2", toolCalls, metadata);

        // Assert
        Assert.NotNull(content1.Metadata);
        Assert.Single(content1.Metadata);

        Assert.NotNull(content2.Metadata);
        Assert.Equal(2, content2.Metadata.Count);
        Assert.Equal("value", content2.Metadata["key"]);

        Assert.IsType<List<ChatToolCall>>(content2.Metadata["ChatResponseMessage.FunctionToolCalls"]);

        var actualToolCalls = content2.Metadata["ChatResponseMessage.FunctionToolCalls"] as List<ChatToolCall>;
        Assert.NotNull(actualToolCalls);

        Assert.Equal(2, actualToolCalls.Count);
        Assert.Equal("id1", actualToolCalls[0].Id);
        Assert.Equal("id2", actualToolCalls[1].Id);
    }

    private void AssertChatMessageContent(
        AuthorRole expectedRole,
        string expectedContent,
        string expectedModelId,
        IReadOnlyList<ChatToolCall> expectedToolCalls,
        OpenAIChatMessageContent actualContent,
        string? expectedName = null)
    {
        Assert.Equal(expectedRole, actualContent.Role);
        Assert.Equal(expectedContent, actualContent.Content);
        Assert.Equal(expectedName, actualContent.AuthorName);
        Assert.Equal(expectedModelId, actualContent.ModelId);
        Assert.Same(expectedToolCalls, actualContent.ToolCalls);
    }

    private sealed class CustomReadOnlyDictionary<TKey, TValue>(IDictionary<TKey, TValue> dictionary) : IReadOnlyDictionary<TKey, TValue> // explicitly not implementing IDictionary<>
    {
        public TValue this[TKey key] => dictionary[key];
        public IEnumerable<TKey> Keys => dictionary.Keys;
        public IEnumerable<TValue> Values => dictionary.Values;
        public int Count => dictionary.Count;
        public bool ContainsKey(TKey key) => dictionary.ContainsKey(key);
        public IEnumerator<KeyValuePair<TKey, TValue>> GetEnumerator() => dictionary.GetEnumerator();
        public bool TryGetValue(TKey key, out TValue value) => dictionary.TryGetValue(key, out value!);
        IEnumerator IEnumerable.GetEnumerator() => dictionary.GetEnumerator();
    }
}
