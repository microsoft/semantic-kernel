// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Text.Json;
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
        List<ChatToolCall> toolCalls = [ChatToolCall.CreateFunctionToolCall("id", "name", BinaryData.FromString("args"))];

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
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());

        List<ChatToolCall> toolCalls = [
            ChatToolCall.CreateFunctionToolCall("id1", "name", BinaryData.FromString(args)),
            ChatToolCall.CreateFunctionToolCall("id2", "name", BinaryData.FromString(args))];

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
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());

        IReadOnlyDictionary<string, object?> metadata = readOnlyMetadata ?
            new CustomReadOnlyDictionary<string, object?>(new Dictionary<string, object?> { { "key", "value" } }) :
            new Dictionary<string, object?> { { "key", "value" } };

        List<ChatToolCall> toolCalls = [
            ChatToolCall.CreateFunctionToolCall("id1", "name", BinaryData.FromString(args)),
            ChatToolCall.CreateFunctionToolCall("id2", "name", BinaryData.FromString(args))];

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
