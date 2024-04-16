// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Azure;
using Xunit;

namespace SemanticKernel.Connectors.Azure.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureStreamingChatMessageContent"/> class.
/// </summary>
public sealed class AzureStreamingChatMessageContentTests
{
    [Fact]
    public void ToByteArrayWorksCorrectly()
    {
        // Arrange
        var expectedBytes = Encoding.UTF8.GetBytes("content");
        var content = new AzureStreamingChatMessageContent(AuthorRole.Assistant, "content", completionsFinishReason: null, 0, "model-id");

        // Act
        var actualBytes = content.ToByteArray();

        // Assert
        Assert.Equal(expectedBytes, actualBytes);
    }

    [Theory]
    [InlineData(null, "")]
    [InlineData("content", "content")]
    public void ToStringWorksCorrectly(string? content, string expectedString)
    {
        // Arrange
        var textContent = new AzureStreamingChatMessageContent(AuthorRole.Assistant, content!, completionsFinishReason: null, 0, "model-id");

        // Act
        var actualString = textContent.ToString();

        // Assert
        Assert.Equal(expectedString, actualString);
    }
}
