// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.AzureSdk;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIWithDataChatMessageContent"/> class.
/// </summary>
public sealed class AzureOpenAIWithDataChatMessageContentTests
{
    [Fact]
    public void ConstructorThrowsExceptionWhenAssistantMessageIsNotProvided()
    {
        // Arrange
        var choice = new ChatWithDataChoice();

        // Act & Assert
        var exception = Assert.Throws<ArgumentException>(() => new AzureOpenAIWithDataChatMessageContent(choice, "model-id"));

        Assert.Contains("Chat is not valid", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void ConstructorReturnsInstanceWithNullToolContent()
    {
        // Arrange
        var choice = new ChatWithDataChoice { Messages = [new() { Content = "Assistant content", Role = "assistant" }] };

        // Act
        var content = new AzureOpenAIWithDataChatMessageContent(choice, "model-id");

        // Assert
        Assert.Equal("Assistant content", content.Content);
        Assert.Equal(AuthorRole.Assistant, content.Role);

        Assert.Null(content.ToolContent);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorReturnsInstanceWithNonNullToolContent(bool includeMetadata)
    {
        // Arrange
        var choice = new ChatWithDataChoice
        {
            Messages = [
                new() { Content = "Assistant content", Role = "assistant" },
                new() { Content = "Tool content", Role = "tool" }]
        };

        // Act
        var content = includeMetadata ?
            new AzureOpenAIWithDataChatMessageContent(choice, "model-id", new Dictionary<string, object?>()) :
            new AzureOpenAIWithDataChatMessageContent(choice, "model-id");

        // Assert
        Assert.Equal("Assistant content", content.Content);
        Assert.Equal("Tool content", content.ToolContent);
        Assert.Equal(AuthorRole.Assistant, content.Role);

        Assert.NotNull(content.Metadata);
        Assert.Equal("Tool content", content.Metadata["ToolContent"]);
    }
}
