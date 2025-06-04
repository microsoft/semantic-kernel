// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Text;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities;

public sealed class StreamJsonParserTests
{
    private const string SeeTestData =
        """
        data: {"candidates": [{"content": {"parts": [{"text": "lorem ipsum"}],"role": "model"},"finishReason": "STOP","index": 0,"safetyRatings": [{"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_HATE_SPEECH","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_HARASSMENT","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_DANGEROUS_CONTENT","probability": "NEGLIGIBLE"}]}],"promptFeedback": {"safetyRatings": [{"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_HATE_SPEECH","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_HARASSMENT","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_DANGEROUS_CONTENT","probability": "NEGLIGIBLE"}]}}

        data: {"candidates": [{"content": {"parts": [{"text": "lorem ipsum"}],"role": "model"},"finishReason": "STOP","index": 0,"safetyRatings": [{"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_HATE_SPEECH","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_HARASSMENT","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_DANGEROUS_CONTENT","probability": "NEGLIGIBLE"}]}]}

        data: {"candidates": [{"content": {"parts": [{"text": " lorem ipsum"}],"role": "model"},"finishReason": "STOP","index": 0,"safetyRatings": [{"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_HATE_SPEECH","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_HARASSMENT","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_DANGEROUS_CONTENT","probability": "NEGLIGIBLE"}]}]}

        data: {"candidates": [{"finishReason": "SAFETY","index": 0,"safetyRatings": [{"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT","probability": "HIGH"},{"category": "HARM_CATEGORY_HATE_SPEECH","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_HARASSMENT","probability": "NEGLIGIBLE"},{"category": "HARM_CATEGORY_DANGEROUS_CONTENT","probability": "NEGLIGIBLE"}]}]}

        """;

    [Fact]
    public async Task ParseSseStreamReturnsEnumerableWithFourObjectsAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        WriteToStream(stream, SeeTestData);

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

        // Assert
        Assert.Equal(4, result.Count);
    }

    [Fact]
    public async Task ParseSseStreamReturnsEnumerableWhereEachLineStartsAndEndsWithBracketAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        WriteToStream(stream, SeeTestData);

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

        // Assert
        Assert.All(result, json => Assert.StartsWith("{", json, StringComparison.Ordinal));
        Assert.All(result, json => Assert.EndsWith("}", json, StringComparison.Ordinal));
    }

    [Fact]
    public async Task ParseWhenStreamStartsWithClosedBracketThrowsInvalidOperationAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = "}{}";
        WriteToStream(stream, input);

        // Act
        // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
        async Task Act() => await parser.ParseAsync(stream).ToListAsync();

        // Assert
        await Assert.ThrowsAnyAsync<InvalidOperationException>(Act);
    }

    [Fact]
    public async Task ParseWhenStreamIsEmptyReturnsEmptyEnumerableAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public async Task ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"bar"}""";
        WriteToStream(stream, input);

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public async Task ParseWhenStreamContainsArrayWithOnlyOneObjectReturnsEnumerableWithOneObjectAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"bar"}""";
        WriteToStream(stream, $"[{input}]");

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public async Task ParseWhenStreamContainsArrayOfTwoObjectsReturnsEnumerableWithTwoObjectsAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        using var stream = new MemoryStream();
        string firstInput = """{"foo":"bar"}""";
        string secondInput = """{"foods":"base"}""";
        WriteToStream(stream, $"[{firstInput},{secondInput}]");

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

        // Assert
        Assert.Collection(result,
            json => Assert.Equal(firstInput, json),
            json => Assert.Equal(secondInput, json));
    }

    [Fact]
    public async Task ParseWhenStreamContainsArrayOfTwoObjectsWithNestedObjectsReturnsEnumerableWithTwoObjectsAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        using var stream = new MemoryStream();
        string firstInput = """{"foo":"bar","nested":{"foo":"bar"}}""";
        string secondInput = """{"foods":"base","nested":{"foo":"bar"}}""";
        WriteToStream(stream, $"[{firstInput},{secondInput}]");

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

        // Assert
        Assert.Collection(result,
            json => Assert.Equal(firstInput, json),
            json => Assert.Equal(secondInput, json));
    }

    [Fact]
    public async Task ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectWithEscapedQuotesAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"be\"r"}""";
        WriteToStream(stream, input);

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public async Task ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectWithEscapedBackslashAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"be\\r"}""";
        WriteToStream(stream, input);

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

        // Assert
        Assert.Single(result, json => input.Equals(json, StringComparison.Ordinal));
    }

    [Fact]
    public async Task ParseWhenStreamContainsOneObjectReturnsEnumerableWithOneObjectWithEscapedBackslashAndQuotesAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        string input = """{"foo":"be\\\"r"}""";
        WriteToStream(stream, input);

        // Act
        var result = await parser.ParseAsync(stream).ToListAsync();

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
