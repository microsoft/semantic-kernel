// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Microsoft.SemanticKernel.Text;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini;

#pragma warning disable CS0419 // Ambiguous StreamJsonParser reference in cref attribute (InternalUtilities)
#pragma warning disable CS1574 // XML comment has cref StreamJsonParser that could not be resolved (InternalUtilities)

/// <summary>
/// Tests for parsing <see cref="GeminiResponse"/> with <see cref="StreamJsonParser"/>.
/// </summary>
public sealed class GeminiStreamResponseTests
{
    private const string StreamTestDataFilePath = "./TestData/chat_stream_response.json";

    [Fact]
    public async Task SerializationShouldPopulateAllPropertiesAsync()
    {
        // Arrange
        var parser = new StreamJsonParser();
        var stream = new MemoryStream();
        var streamExample = await File.ReadAllTextAsync(StreamTestDataFilePath);
        var sampleResponses = JsonSerializer.Deserialize<List<GeminiResponse>>(streamExample)!;

        WriteToStream(stream, streamExample);

        // Act
        var jsonChunks = await parser.ParseAsync(stream).ToListAsync();
        var responses = jsonChunks.Select(json => JsonSerializer.Deserialize<GeminiResponse>(json));

        // Assert
        // Uses all because Equivalent ignores order
        Assert.All(responses, (res, i) => Assert.Equivalent(sampleResponses[i], res));
    }

    private static void WriteToStream(Stream stream, string input)
    {
        using var writer = new StreamWriter(stream, leaveOpen: true);
        writer.Write(input);
        writer.Flush();
        stream.Position = 0;
    }
}
