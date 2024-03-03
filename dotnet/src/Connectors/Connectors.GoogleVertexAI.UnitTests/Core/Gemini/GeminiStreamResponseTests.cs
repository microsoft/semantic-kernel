// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini;

/// <summary>
/// Tests for parsing <see cref="GeminiResponse"/> with <see cref="GeminiStreamJsonParser"/>.
/// </summary>
public sealed class GeminiStreamResponseTests
{
    private const string StreamTestDataFilePath = "./TestData/chat_stream_response.json";

    [Fact]
    public void SerializationShouldPopulateAllProperties()
    {
        // Arrange
        var parser = new GeminiStreamJsonParser();
        var stream = new MemoryStream();
        var streamExample = File.ReadAllText(StreamTestDataFilePath);
        var geminiSampleResponses = JsonSerializer.Deserialize<List<GeminiResponse>>(streamExample);

        WriteToStream(stream, streamExample);

        // Act
        var jsonChunks = parser.Parse(stream);
        var responses = jsonChunks.Select(json => JsonSerializer.Deserialize<GeminiResponse>(json)).ToList();

        // Assert
        Assert.Equivalent(geminiSampleResponses, responses);
    }

    private static void WriteToStream(Stream stream, string input)
    {
        using var writer = new StreamWriter(stream, leaveOpen: true);
        writer.Write(input);
        writer.Flush();
        stream.Position = 0;
    }
}
