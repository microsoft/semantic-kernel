// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Functions.OpenAPI.Builders.Serialization;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI.Builders.Serialization;
public class ArrayParameterSerializerTests
{
    [Fact]
    public void ItShouldCreateParameterPerArrayItem()
    {
        // Arrange
        var array = new JsonArray(1, 2, 3);

        // Act
        var result = ArrayParameterValueSerializer.SerializeArrayAsSeparateParameters("id", array, delimiter: "&");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1&id=2&id=3", result);
    }

    [Fact]
    public void ItShouldAllowDuplicatesWhenCreatingParameterPerArrayItem()
    {
        // Arrange
        var array = new JsonArray(1, 2, 2, 3);

        // Act
        var result = ArrayParameterValueSerializer.SerializeArrayAsSeparateParameters("id", array, delimiter: "&");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1&id=2&id=2&id=3", result);
    }

    [Fact]
    public void ItShouldAllowParameterDelimiterAsValueWhenCreatingParameterPerArrayItem()
    {
        // Arrange
        var array = new JsonArray("a", "b&", "c");

        // Act
        var result = ArrayParameterValueSerializer.SerializeArrayAsSeparateParameters("id", array, delimiter: "&");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=a&id=b%26&id=c", result);
    }

    [Fact]
    public void ItShouldCreateParameterWithDelimitedValuePerArrayItem()
    {
        // Arrange
        var array = new JsonArray(1, 2, 3);

        // Act
        var result = ArrayParameterValueSerializer.SerializeArrayAsDelimitedValues(array, delimiter: "%20");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("1%202%203", result);
    }

    [Fact]
    public void ItShouldAllowDuplicatesWhenCreatingParameterWithDelimitedValuePerArrayItem()
    {
        // Arrange
        var array = new JsonArray(1, 2, 2, 3);

        // Act
        var result = ArrayParameterValueSerializer.SerializeArrayAsDelimitedValues(array, delimiter: "%20");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("1%202%202%203", result);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInSeparateParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var array = new JsonArray($"{specialSymbol}");

        // Act
        var result = ArrayParameterValueSerializer.SerializeArrayAsSeparateParameters("id", array, delimiter: "&");

        // Assert
        Assert.NotNull(result);

        Assert.EndsWith(encodedEquivalent, result, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInDelimitedParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var array = new JsonArray($"{specialSymbol}");

        // Act
        var result = ArrayParameterValueSerializer.SerializeArrayAsDelimitedValues(array, delimiter: "%20");

        // Assert
        Assert.NotNull(result);

        Assert.EndsWith(encodedEquivalent, result, StringComparison.Ordinal);
    }
}
