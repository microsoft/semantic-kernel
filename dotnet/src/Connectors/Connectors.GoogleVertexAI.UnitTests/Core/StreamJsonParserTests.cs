// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core;

public sealed class StreamJsonParserTests
{
    [Fact]
    public void ParseWhenStreamIsEmptyReturnsEmptyEnumerable()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();

        // Act
        var result = parser.ParseAsync(stream);

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public void ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObject()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"bar"}""";
        WriteToStream(stream, input);

        // Act
        var result = parser.ParseAsync(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public void ParseWhenStreamContainsArrayWithOnlyOneObjectReturnsEnumerableWithOneObject()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"bar"}""";
        WriteToStream(stream, $"[{input}]");

        // Act
        var result = parser.ParseAsync(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public void ParseWhenStreamContainsArrayOfTwoObjectsReturnsEnumerableWithTwoObjects()
    {
        // Arrange
        var parser = new StreamJsonParser();
        using var stream = new MemoryStream();
        string firstInput = """{"foo":"bar"}""";
        string secondInput = """{"foods":"base"}""";
        WriteToStream(stream, $"[{firstInput},{secondInput}]");

        // Act
        var result = parser.ParseAsync(stream);

        // Assert
        Assert.Collection(result,
            json => Assert.Equal(firstInput, json),
            json => Assert.Equal(secondInput, json));
    }

    [Fact]
    public void ParseWhenStreamContainsArrayOfTwoObjectsWithNestedObjectsReturnsEnumerableWithTwoObjects()
    {
        // Arrange
        var parser = new StreamJsonParser();
        using var stream = new MemoryStream();
        string firstInput = """{"foo":"bar","nested":{"foo":"bar"}}""";
        string secondInput = """{"foods":"base","nested":{"foo":"bar"}}""";
        WriteToStream(stream, $"[{firstInput},{secondInput}]");

        // Act
        var result = parser.ParseAsync(stream);

        // Assert
        Assert.Collection(result,
            json => Assert.Equal(firstInput, json),
            json => Assert.Equal(secondInput, json));
    }

    [Fact]
    public void ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectWithEscapedQuotes()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"be\"r"}""";
        WriteToStream(stream, input);

        // Act
        var result = parser.ParseAsync(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public void ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectWithEscapedBackslash()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"be\\r"}""";
        WriteToStream(stream, input);

        // Act
        var result = parser.ParseAsync(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public void ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectWithEscapedBackslashAndQuotes()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"be\\\"r"}""";
        WriteToStream(stream, input);

        // Act
        var result = parser.ParseAsync(stream);

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public async Task ParseWithJsonValidationWhenStreamContainsInvalidJsonThrowsJsonExceptionAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":,"bar"}""";
        WriteToStream(stream, input);

        // Act
        // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
        async Task Act() => await parser.ParseAsync(stream, validateJson: true).ToListAsync();

        // Assert
        await Assert.ThrowsAnyAsync<JsonException>(Act);
    }

    [Fact]
    public async Task ParseWithoutJsonValidationWhenStreamContainsInvalidJsonDoesntThrowAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":,"bar"}""";
        WriteToStream(stream, input);

        // Act & Assert
        await parser.ParseAsync(stream, validateJson: false).ToListAsync();
        // We don't need to use Assert here, because we are testing that the method doesn't throw
    }

    private static void WriteToStream(Stream stream, string input)
    {
        using var writer = new StreamWriter(stream, leaveOpen: true);
        writer.Write(input);
        writer.Flush();
        stream.Position = 0;
    }
}
