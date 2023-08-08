// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace SemanticKernel.UnitTests.Text;

/// <summary>
/// Unit tests for StringExtensions
/// </summary>
public class StringExtensionsTests
{
    [Theory]
    [InlineData("\r\n", "\n")]
    [InlineData("Test string\r\n", "Test string\n")]
    [InlineData("\r\nTest string", "\nTest string")]
    [InlineData("\r\nTest string\r\n", "\nTest string\n")]
    public void ItNormalizesLineEndingsCorrectly(string input, string expectedString)
    {
        // Act
        input = input.ReplaceLineEndingsWithLineFeed();

        // Assert
        Assert.Equal(expectedString, input);
    }
}
