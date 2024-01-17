// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

/// <summary>
/// Unit tests for <see cref="ImageContent"/> class.
/// </summary>
public sealed class ImageContentTests
{
    [Fact]
    public void ToStringReturnsString()
    {
        // Arrange
        var content1 = new ImageContent(null!);
        var content2 = new ImageContent(new Uri("https://endpoint/"));

        // Act
        var result1 = content1.ToString();
        var result2 = content2.ToString();

        // Assert
        Assert.Empty(result1);
        Assert.Equal("https://endpoint/", result2);
    }
}
