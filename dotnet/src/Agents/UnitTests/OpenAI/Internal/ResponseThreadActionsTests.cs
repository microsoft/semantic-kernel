// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Internal;

/// <summary>
/// Unit tests for <see cref="ResponseThreadActions"/>.
/// </summary>
public class ResponseThreadActionsTests
{
    /// <summary>
    /// Verify that <see cref="ResponseThreadActions.GetFunctionResultAsString(object?)"/> returns the
    /// shared <c>ImageContentNotSupportedErrorMessage</c> when the function result is an
    /// <see cref="ImageContent"/>, since the OpenAI Responses API does not support multimodal tool results.
    /// </summary>
    [Fact]
    public void VerifyResponseThreadActionsGetFunctionResultAsStringReturnsErrorMessageForImageContent()
    {
        // Arrange: Create an ImageContent with binary data
        var imageData = new ReadOnlyMemory<byte>([0x89, 0x50, 0x4E, 0x47]); // PNG magic bytes
        var imageContent = new ImageContent(imageData, "image/png");

        // Act
        string result = ResponseThreadActions.GetFunctionResultAsString(imageContent);

        // Assert
        Assert.Equal("Error: This model does not support image content in tool results.", result);
    }

    /// <summary>
    /// Verify that <see cref="ResponseThreadActions.GetFunctionResultAsString(object?)"/> returns the
    /// original string verbatim when the function result is a string.
    /// </summary>
    [Fact]
    public void VerifyResponseThreadActionsGetFunctionResultAsStringReturnsStringVerbatim()
    {
        // Arrange
        const string Expected = "tool result text";

        // Act
        string result = ResponseThreadActions.GetFunctionResultAsString(Expected);

        // Assert
        Assert.Equal(Expected, result);
    }

    /// <summary>
    /// Verify that <see cref="ResponseThreadActions.GetFunctionResultAsString(object?)"/> returns
    /// <see cref="string.Empty"/> when the function result is <see langword="null"/>.
    /// </summary>
    [Fact]
    public void VerifyResponseThreadActionsGetFunctionResultAsStringReturnsEmptyForNull()
    {
        // Act
        string result = ResponseThreadActions.GetFunctionResultAsString(null);

        // Assert
        Assert.Equal(string.Empty, result);
    }
}
