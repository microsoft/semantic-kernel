// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Client;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests.TextGeneration;

public sealed class TextGenerationStreamJsonParserTests
{
    [Fact]
    public void ParseWhenStreamIsEmptyReturnsEmptyEnumerable()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        var stream = new MemoryStream();

        // Act
        var result = parser.Parse(stream);

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public void ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObject()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"bar"}""";
        WriteToStream(stream, input);

        // Act
        var result = parser.Parse(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public void ParseWhenStreamContainsArrayWithOnlyOneObjectReturnsEnumerableWithOneObject()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"bar"}""";
        WriteToStream(stream, $"[{input}]");

        // Act
        var result = parser.Parse(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public void ParseWhenStreamContainsArrayOfTwoObjectsReturnsEnumerableWithTwoObjects()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        using var stream = new MemoryStream();
        string firstInput = """{"foo":"bar"}""";
        string secondInput = """{"foods":"base"}""";
        WriteToStream(stream, $"[{firstInput},{secondInput}]");

        // Act
        var result = parser.Parse(stream);

        // Assert
        Assert.Collection(result,
            json => Assert.Equal(firstInput, json),
            json => Assert.Equal(secondInput, json));
    }

    [Fact]
    public void ParseWhenStreamContainsArrayOfTwoObjectsWithNestedObjectsReturnsEnumerableWithTwoObjects()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        using var stream = new MemoryStream();
        string firstInput = """{"foo":"bar","nested":{"foo":"bar"}}""";
        string secondInput = """{"foods":"base","nested":{"foo":"bar"}}""";
        WriteToStream(stream, $"[{firstInput},{secondInput}]");

        // Act
        var result = parser.Parse(stream);

        // Assert
        Assert.Collection(result,
            json => Assert.Equal(firstInput, json),
            json => Assert.Equal(secondInput, json));
    }

    [Fact]
    public void ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectWithEscapedQuotes()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"be\"r"}""";
        WriteToStream(stream, input);

        // Act
        var result = parser.Parse(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public void ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectWithEscapedBackslash()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"be\\r"}""";
        WriteToStream(stream, input);

        // Act
        var result = parser.Parse(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public void ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectWithEscapedBackslashAndQuotes()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"be\\\"r"}""";
        WriteToStream(stream, input);

        // Act
        var result = parser.Parse(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public void ParseWithJsonValidationWhenStreamContainsInvalidJsonThrowsJsonException()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":,"bar"}""";
        WriteToStream(stream, input);

        // Act
        void Act() => parser.Parse(stream, validateJson: true).ToList();

        // Assert
        Assert.ThrowsAny<JsonException>(Act);
    }

    [Fact]
    public void ParseWithoutJsonValidationWhenStreamContainsInvalidJsonDoesntThrow()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":,"bar"}""";
        WriteToStream(stream, input);

        // Act
        var exception = Record.Exception(() => parser.Parse(stream, validateJson: false).ToList());

        // Assert
        Assert.Null(exception);
    }

    private static void WriteToStream(Stream stream, string input)
    {
        using var writer = new StreamWriter(stream, leaveOpen: true);
        writer.Write(input);
        writer.Flush();
        stream.Position = 0;
    }
}
