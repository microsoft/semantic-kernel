// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Core;

public class TextPluginTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        var _ = new TextPlugin();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs e.g. due to reflection
        kernel.ImportPlugin(new TextPlugin(), "text");
    }

    [Fact]
    public void ItCanTrim()
    {
        // Arrange
        var plugin = new TextPlugin();

        // Act
        var result = plugin.Trim("  hello world  ");

        // Assert
        Assert.Equal("hello world", result);
    }

    [Fact]
    public void ItCanTrimStart()
    {
        // Arrange
        var plugin = new TextPlugin();

        // Act
        var result = plugin.TrimStart("  hello world  ");

        // Assert
        Assert.Equal("hello world  ", result);
    }

    [Fact]
    public void ItCanTrimEnd()
    {
        // Arrange
        var plugin = new TextPlugin();

        // Act
        var result = plugin.TrimEnd("  hello world  ");

        // Assert
        Assert.Equal("  hello world", result);
    }

    [Fact]
    public void ItCanUppercase()
    {
        // Arrange
        var plugin = new TextPlugin();

        // Act
        var result = plugin.Uppercase("hello world");

        // Assert
        Assert.Equal("HELLO WORLD", result);
    }

    [Fact]
    public void ItCanLowercase()
    {
        // Arrange
        var plugin = new TextPlugin();

        // Act
        var result = plugin.Lowercase("HELLO WORLD");

        // Assert
        Assert.Equal("hello world", result);
    }

    [Theory]
    [InlineData("hello world ", 12)]
    [InlineData("hello World", 11)]
    [InlineData("HELLO", 5)]
    [InlineData("World", 5)]
    [InlineData("", 0)]
    [InlineData(" ", 1)]
    [InlineData(null, 0)]
    public void ItCanLength(string textToLength, int expectedLength)
    {
        // Arrange
        var target = new TextPlugin();

        // Act
        var result = target.Length(textToLength);

        // Assert
        Assert.Equal(expectedLength, result);
    }

    [Theory]
    [InlineData("hello world", "hello world")]
    [InlineData("hello World", "hello World")]
    [InlineData("HELLO", "HELLO")]
    [InlineData("World", "World")]
    [InlineData("", "")]
    [InlineData(" ", " ")]
    [InlineData(null, "")]
    public void ItCanConcat(string textToConcat, string text2ToConcat)
    {
        // Arrange
        var target = new TextPlugin();
        var expected = string.Concat(textToConcat, text2ToConcat);

        // Act
        string result = target.Concat(textToConcat, text2ToConcat);

        // Assert
        Assert.Equal(expected, result);
    }
}
