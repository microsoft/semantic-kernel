// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Core;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIStreamingTextContent"/> class.
/// </summary>
public sealed class AzureOpenAIStreamingTextContentTests
{
    [Fact]
    public void ToByteArrayWorksCorrectly()
    {
        // Arrange
        var expectedBytes = Encoding.UTF8.GetBytes("content");
        var content = new AzureOpenAIStreamingTextContent("content", 0, "model-id");

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
        var textContent = new AzureOpenAIStreamingTextContent(content!, 0, "model-id");

        // Act
        var actualString = textContent.ToString();

        // Assert
        Assert.Equal(expectedString, actualString);
    }
}
