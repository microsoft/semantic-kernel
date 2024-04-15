// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.AzureSdk;

/// <summary>
/// Unit tests for <see cref="OpenAIStreamingTextContent"/> class.
/// </summary>
public sealed class OpenAIStreamingTextContentTests
{
    [Fact]
    public void ToByteArrayWorksCorrectly()
    {
        // Arrange
        var expectedBytes = Encoding.UTF8.GetBytes("content");
        var content = new OpenAIStreamingTextContent("content", 0, "model-id");

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
        var textContent = new OpenAIStreamingTextContent(content!, 0, "model-id");

        // Act
        var actualString = textContent.ToString();

        // Assert
        Assert.Equal(expectedString, actualString);
    }
}
