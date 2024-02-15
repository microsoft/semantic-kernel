// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.AzureSdk;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIWithDataStreamingChatMessageContent"/> class.
/// </summary>
public sealed class AzureOpenAIWithDataStreamingChatMessageContentTests
{
    [Theory]
    [MemberData(nameof(ValidChoices))]
    public void ConstructorWithValidChoiceSetsNonEmptyContent(object choice, string expectedContent)
    {
        // Arrange
        var streamingChoice = choice as ChatWithDataStreamingChoice;

        // Act
        var content = new AzureOpenAIWithDataStreamingChatMessageContent(streamingChoice!, 0, "model-id");

        // Assert
        Assert.Equal(expectedContent, content.Content);
    }

    [Theory]
    [MemberData(nameof(InvalidChoices))]
    public void ConstructorWithInvalidChoiceSetsNullContent(object choice)
    {
        // Arrange
        var streamingChoice = choice as ChatWithDataStreamingChoice;

        // Act
        var content = new AzureOpenAIWithDataStreamingChatMessageContent(streamingChoice!, 0, "model-id");

        // Assert
        Assert.Null(content.Content);
    }

    public static IEnumerable<object[]> ValidChoices
    {
        get
        {
            yield return new object[] { new ChatWithDataStreamingChoice { Messages = [new() { Delta = new() { Content = "Content 1" } }] }, "Content 1" };
            yield return new object[] { new ChatWithDataStreamingChoice { Messages = [new() { Delta = new() { Content = "Content 2", Role = "Assistant" } }] }, "Content 2" };
        }
    }

    public static IEnumerable<object[]> InvalidChoices
    {
        get
        {
            yield return new object[] { new ChatWithDataStreamingChoice { Messages = [new() { EndTurn = true }] } };
            yield return new object[] { new ChatWithDataStreamingChoice { Messages = [new() { Delta = new() { Content = "Content", Role = "tool" } }] } };
        }
    }
}
