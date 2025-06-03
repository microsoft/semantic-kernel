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
    public void InternalConstructorInitializesCorrectlyForSerialization()
    {
        // Arrange & Act - Test that serialization/deserialization works with internal constructor
        var originalContent = new OpenAIChatMessageContent(AuthorRole.Assistant, "Test message", "gpt-4", []);

        var json = JsonSerializer.Serialize(originalContent);
        var deserializedContent = JsonSerializer.Deserialize<OpenAIChatMessageContent>(json);

        // Assert - Verify that deserialization properly initializes the object
        Assert.NotNull(deserializedContent);
        Assert.NotNull(deserializedContent.ToolCalls);
        Assert.Empty(deserializedContent.ToolCalls);
        Assert.Equal("assistant", deserializedContent.Role.Label);
        Assert.Equal("Test message", deserializedContent.Content);
        Assert.Equal("gpt-4", deserializedContent.ModelId);
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

    [Fact]
    public void SerializationWithoutToolCallsWorksCorrectly()
    {
        // Arrange
        var originalContent = new OpenAIChatMessageContent(AuthorRole.Assistant, "Hello, world!", "gpt-4", [])
        {
            AuthorName = "Assistant"
        };

        // Act
        var json = JsonSerializer.Serialize(originalContent);
        var deserializedContent = JsonSerializer.Deserialize<OpenAIChatMessageContent>(json);

        // Assert
        Assert.NotNull(deserializedContent);
        Assert.Equal(originalContent.Role.Label, deserializedContent.Role.Label);
        Assert.Equal(originalContent.Content, deserializedContent.Content);
        Assert.Equal(originalContent.AuthorName, deserializedContent.AuthorName);
        Assert.Equal(originalContent.ModelId, deserializedContent.ModelId);
        Assert.NotNull(deserializedContent.ToolCalls);
        Assert.Empty(deserializedContent.ToolCalls);
    }

    [Fact]
    public void SerializationWithoutToolCallsWorksCorrectlyForBasicScenario()
    {
        // Arrange - Test the basic scenario without tool calls which is the main use case for serialization
        var originalContent = new OpenAIChatMessageContent(AuthorRole.Assistant, "I'll help you with that.", "gpt-4", [])
        {
            AuthorName = "Assistant"
        };

        // Act
        var json = JsonSerializer.Serialize(originalContent);
        var deserializedContent = JsonSerializer.Deserialize<OpenAIChatMessageContent>(json);

        // Assert
        Assert.NotNull(deserializedContent);
        Assert.Equal(originalContent.Role.Label, deserializedContent.Role.Label);
        Assert.Equal(originalContent.Content, deserializedContent.Content);
        Assert.Equal(originalContent.AuthorName, deserializedContent.AuthorName);
        Assert.Equal(originalContent.ModelId, deserializedContent.ModelId);
        Assert.NotNull(deserializedContent.ToolCalls);
        Assert.Empty(deserializedContent.ToolCalls);
    }

    [Fact]
    public void SerializationWithToolRoleWorksCorrectly()
    {
        // Arrange - This simulates the scenario from the issue where Tool role messages need to be serialized
        var originalContent = new OpenAIChatMessageContent(AuthorRole.Tool, "Function result data", "gpt-4", []);

        // Act
        var json = JsonSerializer.Serialize(originalContent);
        var deserializedContent = JsonSerializer.Deserialize<OpenAIChatMessageContent>(json);

        // Assert
        Assert.NotNull(deserializedContent);
        Assert.Equal(AuthorRole.Tool.Label, deserializedContent.Role.Label);
        Assert.Equal(originalContent.Content, deserializedContent.Content);
        Assert.Equal(originalContent.ModelId, deserializedContent.ModelId);
        Assert.NotNull(deserializedContent.ToolCalls);
        Assert.Empty(deserializedContent.ToolCalls);
    }

    [Fact]
    public void SerializationPreservesAllProperties()
    {
        // Arrange - Test that all properties are properly preserved during serialization/deserialization
        var originalContent = new OpenAIChatMessageContent(AuthorRole.Assistant, "Test content", "gpt-4", [])
        {
            AuthorName = "TestBot"
        };

        // Act
        var json = JsonSerializer.Serialize(originalContent);
        var deserializedContent = JsonSerializer.Deserialize<OpenAIChatMessageContent>(json);

        // Assert
        Assert.NotNull(deserializedContent);
        Assert.Equal("assistant", deserializedContent.Role.Label);
        Assert.Equal("gpt-4", deserializedContent.ModelId);
        Assert.Equal("Test content", deserializedContent.Content);
        Assert.Equal("TestBot", deserializedContent.AuthorName);
        Assert.NotNull(deserializedContent.ToolCalls);
        Assert.Empty(deserializedContent.ToolCalls);
    }

    [Fact]
    public void SerializationWithNonEmptyToolCallsWorksCorrectlyWithJsonConverter()
    {
        // Arrange - Test that serialization with actual tool calls works with custom JsonConverter
        // Note: ToolCalls property now uses a custom JsonConverter to handle ChatToolCall serialization
        var args = JsonSerializer.Serialize(new Dictionary<string, object?> { { "location", "Seattle" }, { "unit", "celsius" } });
        List<ChatToolCall> toolCalls = [
            ChatToolCall.CreateFunctionToolCall("tool-call-1", "get_weather", BinaryData.FromString(args)),
            ChatToolCall.CreateFunctionToolCall("tool-call-2", "get_time", BinaryData.FromString("{\"timezone\":\"PST\"}")),
            ChatToolCall.CreateFunctionToolCall("tool-call-3", "get_current_user", BinaryData.FromString("{}")) // No arguments
        ];

        var originalContent = new OpenAIChatMessageContent(AuthorRole.Assistant, "I'll get the weather and time for you.", "gpt-4", toolCalls)
        {
            AuthorName = "WeatherBot"
        };

        // Act - Serialization and deserialization should work now
        var json = JsonSerializer.Serialize(originalContent);
        var deserializedContent = JsonSerializer.Deserialize<OpenAIChatMessageContent>(json);

        // Assert - Verify that serialization works and ToolCalls are properly serialized/deserialized
        Assert.NotNull(json);
        Assert.Contains("ToolCalls", json); // ToolCalls should be serialized

        Assert.NotNull(deserializedContent);
        Assert.Equal("assistant", deserializedContent.Role.Label);
        Assert.Equal("gpt-4", deserializedContent.ModelId);
        Assert.Equal("I'll get the weather and time for you.", deserializedContent.Content);
        Assert.Equal("WeatherBot", deserializedContent.AuthorName);

        // ToolCalls should be properly deserialized
        Assert.NotNull(deserializedContent.ToolCalls);
        Assert.Equal(3, deserializedContent.ToolCalls.Count);

        // Verify first tool call (with arguments)
        Assert.Equal("tool-call-1", deserializedContent.ToolCalls[0].Id);
        Assert.Equal("get_weather", deserializedContent.ToolCalls[0].FunctionName);
        Assert.Equal(args, deserializedContent.ToolCalls[0].FunctionArguments.ToString());

        // Verify second tool call (with arguments)
        Assert.Equal("tool-call-2", deserializedContent.ToolCalls[1].Id);
        Assert.Equal("get_time", deserializedContent.ToolCalls[1].FunctionName);
        Assert.Equal("{\"timezone\":\"PST\"}", deserializedContent.ToolCalls[1].FunctionArguments.ToString());

        // Verify third tool call (without arguments)
        Assert.Equal("tool-call-3", deserializedContent.ToolCalls[2].Id);
        Assert.Equal("get_current_user", deserializedContent.ToolCalls[2].FunctionName);
        Assert.Equal("{}", deserializedContent.ToolCalls[2].FunctionArguments.ToString());
    }

    [Fact]
    public void SerializationWithToolCallsEdgeCasesWorksCorrectly()
    {
        // Arrange - Test edge cases for tool call serialization
        List<ChatToolCall> toolCalls = [
            ChatToolCall.CreateFunctionToolCall("tool-1", "no_args_function", BinaryData.FromString("{}")), // Empty object
            ChatToolCall.CreateFunctionToolCall("tool-2", "minimal_function", BinaryData.FromString("")), // Empty string
            ChatToolCall.CreateFunctionToolCall("tool-3", "null_args_function", BinaryData.FromString("null")) // Null value
        ];

        var originalContent = new OpenAIChatMessageContent(AuthorRole.Assistant, "Calling functions with various argument types.", "gpt-4", toolCalls);

        // Act
        var json = JsonSerializer.Serialize(originalContent);
        var deserializedContent = JsonSerializer.Deserialize<OpenAIChatMessageContent>(json);

        // Assert
        Assert.NotNull(deserializedContent);
        Assert.Equal(3, deserializedContent.ToolCalls.Count);

        // Verify empty object arguments
        Assert.Equal("tool-1", deserializedContent.ToolCalls[0].Id);
        Assert.Equal("no_args_function", deserializedContent.ToolCalls[0].FunctionName);
        Assert.Equal("{}", deserializedContent.ToolCalls[0].FunctionArguments.ToString());

        // Verify empty string arguments
        Assert.Equal("tool-2", deserializedContent.ToolCalls[1].Id);
        Assert.Equal("minimal_function", deserializedContent.ToolCalls[1].FunctionName);
        Assert.Equal("", deserializedContent.ToolCalls[1].FunctionArguments.ToString());

        // Verify null arguments
        Assert.Equal("tool-3", deserializedContent.ToolCalls[2].Id);
        Assert.Equal("null_args_function", deserializedContent.ToolCalls[2].FunctionName);
        Assert.Equal("null", deserializedContent.ToolCalls[2].FunctionArguments.ToString());
    }

    [Fact]
    public void SerializationWorksForMostCommonScenarios()
    {
        // Arrange - Test the most common serialization scenarios that work
        // This covers the main use case from issue #11820: saving chat history without active tool calls

        var chatHistory = new List<OpenAIChatMessageContent>
        {
            // User message
            new(AuthorRole.User, "What's the weather like?", "gpt-4", []),

            // Assistant message without tool calls (most common case for serialization)
            new(AuthorRole.Assistant, "I'll check the weather for you.", "gpt-4", []),

            // Tool message (result of a tool call)
            new(AuthorRole.Tool, "Weather data: 72°F, sunny", "gpt-4", [])
        };

        // Act
        var json = JsonSerializer.Serialize(chatHistory);
        var deserializedHistory = JsonSerializer.Deserialize<List<OpenAIChatMessageContent>>(json);

        // Assert
        Assert.NotNull(deserializedHistory);
        Assert.Equal(3, deserializedHistory.Count);

        // Verify all messages were properly serialized and deserialized
        Assert.Equal("user", deserializedHistory[0].Role.Label);
        Assert.Equal("What's the weather like?", deserializedHistory[0].Content);

        Assert.Equal("assistant", deserializedHistory[1].Role.Label);
        Assert.Equal("I'll check the weather for you.", deserializedHistory[1].Content);

        Assert.Equal("tool", deserializedHistory[2].Role.Label);
        Assert.Equal("Weather data: 72°F, sunny", deserializedHistory[2].Content);

        // All should have empty tool calls (which is serializable)
        Assert.All(deserializedHistory, msg => Assert.Empty(msg.ToolCalls));
    }

    [Fact]
    public void ToolRoleMessageSerializationScenario()
    {
        // Arrange - This test specifically addresses the scenario described in issue #11820
        // where Tool role messages with ToolCalls need to be serialized/deserialized for chat history persistence

        // Create a list of OpenAIChatMessageContent objects simulating a chat history with tool calls
        var chatHistory = new List<OpenAIChatMessageContent>
        {
            // User message
            new(AuthorRole.User, "What's the weather like?", "gpt-4", []),

            // Assistant message (this would normally have tool calls, but we'll keep it simple for serialization)
            new(AuthorRole.Assistant, "I'll check the weather for you.", "gpt-4", []),

            // Tool message - this is the specific scenario that was failing in the issue
            new(AuthorRole.Tool, "Weather data: 72°F, sunny", "gpt-4", [])
        };

        // Act - Serialize and deserialize the entire chat history
        var json = JsonSerializer.Serialize(chatHistory);
        var deserializedHistory = JsonSerializer.Deserialize<List<OpenAIChatMessageContent>>(json);

        // Assert - Verify that all messages were properly serialized and deserialized
        Assert.NotNull(deserializedHistory);
        Assert.Equal(3, deserializedHistory.Count);

        // Verify user message
        Assert.Equal("user", deserializedHistory[0].Role.Label);
        Assert.Equal("What's the weather like?", deserializedHistory[0].Content);

        // Verify assistant message
        Assert.Equal("assistant", deserializedHistory[1].Role.Label);
        Assert.Equal("I'll check the weather for you.", deserializedHistory[1].Content);

        // Verify tool message - this was the problematic scenario in issue #11820
        Assert.Equal("tool", deserializedHistory[2].Role.Label);
        Assert.Equal("Weather data: 72°F, sunny", deserializedHistory[2].Content);
        Assert.NotNull(deserializedHistory[2].ToolCalls);
        Assert.Empty(deserializedHistory[2].ToolCalls);
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
