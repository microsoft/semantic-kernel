// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Orchestration.Transforms;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Orchestration;

public class DefaultTransformsTests
{
    [Fact]
    public async Task FromInputAsync_WithEnumerableOfChatMessageContent_ReturnsInputAsync()
    {
        // Arrange
        IEnumerable<ChatMessageContent> input =
        [
            new(AuthorRole.User, "Hello"),
            new(AuthorRole.Assistant, "Hi there")
        ];

        // Act
        IEnumerable<ChatMessageContent> result = await DefaultTransforms.FromInput(input);

        // Assert
        Assert.Equal(input, result);
    }

    [Fact]
    public async Task FromInputAsync_WithChatMessageContent_ReturnsInputAsListAsync()
    {
        // Arrange
        ChatMessageContent input = new(AuthorRole.User, "Hello");

        // Act
        IEnumerable<ChatMessageContent> result = await DefaultTransforms.FromInput(input);

        // Assert
        Assert.Single(result);
        Assert.Equal(input, result.First());
    }

    [Fact]
    public async Task FromInputAsync_WithStringInput_ReturnsUserChatMessageAsync()
    {
        // Arrange
        string input = "Hello, world!";

        // Act
        IEnumerable<ChatMessageContent> result = await DefaultTransforms.FromInput(input);

        // Assert
        Assert.Single(result);
        ChatMessageContent message = result.First();
        Assert.Equal(AuthorRole.User, message.Role);
        Assert.Equal(input, message.Content);
    }

    [Fact]
    public async Task FromInputAsync_WithObjectInput_SerializesAsJsonAsync()
    {
        // Arrange
        TestObject input = new() { Id = 1, Name = "Test" };

        // Act
        IEnumerable<ChatMessageContent> result = await DefaultTransforms.FromInput(input);

        // Assert
        Assert.Single(result);
        ChatMessageContent message = result.First();
        Assert.Equal(AuthorRole.User, message.Role);

        string expectedJson = JsonSerializer.Serialize(input);
        Assert.Equal(expectedJson, message.Content);
    }

    [Fact]
    public async Task ToOutputAsync_WithOutputTypeMatchingInputList_ReturnsSameListAsync()
    {
        // Arrange
        IList<ChatMessageContent> input =
        [
            new(AuthorRole.User, "Hello"),
            new(AuthorRole.Assistant, "Hi there")
        ];

        // Act
        IList<ChatMessageContent> result = await DefaultTransforms.ToOutput<IList<ChatMessageContent>>(input);

        // Assert
        Assert.Same(input, result);
    }

    [Fact]
    public async Task ToOutputAsync_WithOutputTypeChatMessageContent_ReturnsSingleMessageAsync()
    {
        // Arrange
        IList<ChatMessageContent> input =
        [
            new(AuthorRole.User, "Hello")
        ];

        // Act
        ChatMessageContent result = await DefaultTransforms.ToOutput<ChatMessageContent>(input);

        // Assert
        Assert.Same(input[0], result);
    }

    [Fact]
    public async Task ToOutputAsync_WithOutputTypeString_ReturnsContentOfSingleMessageAsync()
    {
        // Arrange
        string expected = "Hello, world!";
        IList<ChatMessageContent> input =
        [
            new(AuthorRole.User, expected)
        ];

        // Act
        string result = await DefaultTransforms.ToOutput<string>(input);

        // Assert
        Assert.Equal(expected, result);
    }

    [Fact]
    public async Task ToOutputAsync_WithOutputTypeDeserializable_DeserializesFromContentAsync()
    {
        // Arrange
        TestObject expected = new() { Id = 42, Name = "TestName" };
        string json = JsonSerializer.Serialize(expected);
        IList<ChatMessageContent> input =
        [
            new(AuthorRole.User, json)
        ];

        // Act
        TestObject result = await DefaultTransforms.ToOutput<TestObject>(input);

        // Assert
        Assert.Equal(expected.Id, result.Id);
        Assert.Equal(expected.Name, result.Name);
    }

    [Fact]
    public async Task ToOutputAsync_WithInvalidJson_ThrowsExceptionAsync()
    {
        // Arrange
        IList<ChatMessageContent> input =
        [
            new(AuthorRole.User, "Not valid JSON")
        ];

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await DefaultTransforms.ToOutput<TestObject>(input)
        );
    }

    [Fact]
    public async Task ToOutputAsync_WithMultipleMessagesAndNonMatchingType_ThrowsExceptionAsync()
    {
        // Arrange
        IList<ChatMessageContent> input =
        [
            new(AuthorRole.User, "Hello"),
            new(AuthorRole.Assistant, "Hi there")
        ];

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await DefaultTransforms.ToOutput<TestObject>(input)
        );
    }

    [Fact]
    public async Task ToOutputAsync_WithNullContent_HandlesGracefullyAsync()
    {
        // Arrange
        IList<ChatMessageContent> input =
        [
            new(AuthorRole.User, (string?)null)
        ];

        // Act
        string result = await DefaultTransforms.ToOutput<string>(input);

        // Assert
        Assert.Equal(string.Empty, result);
    }

    private sealed class TestObject
    {
        public int Id { get; set; }
        public string? Name { get; set; }
    }
}
