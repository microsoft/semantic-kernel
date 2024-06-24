// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Client;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests.TextGeneration;
public class TextGenerationStreamResponseTests
{
    [Fact]
    public void SerializationShouldPopulateAllProperties()
    {
        // Arrange
        var parser = new TextGenerationStreamJsonParser();
        var stream = new MemoryStream();
        var huggingFaceStreamExample = """
                    {
                        "index": 150,
                        "token": {
                            "id": 1178,
                            "text": " data",
                            "logprob": -0.4560547,
                            "special": false
                        },
                        "generated_text": "Write about the difference between Data Science and AI Engineering.\n\nData Science and AI Engineering are two interconnected fields that have gained immense popularity in recent years. While both fields deal with data and machine learning, they have distinct differences in terms of their focus, skills required, and applications.\n\nData Science is a multidisciplinary field that involves the extraction of insights and knowledge from large and complex data sets. It combines various disciplines such as mathematics, statistics, computer science, and domain expertise to analyze and interpret data. Data scientists use a variety of tools and techniques such as data cleaning, data wrangling, data visualization, and machine learning algorithms to derive insights and make informed decisions. They work closely with stakeholders to understand business requirements and translate them into data",
                        "details": null
                    }
                    {
                        "index": 149,
                        "token": {
                            "id": 778,
                            "text": " into",
                            "logprob": -0.000011920929,
                            "special": false
                        },
                        "generated_text": null,
                        "details": null
                    }
                    """;

        WriteToStream(stream, huggingFaceStreamExample);

        // Act
        var chunks = new List<TextGenerationStreamResponse>();
        foreach (var chunk in parser.Parse(stream))
        {
            chunks.Add(JsonSerializer.Deserialize<TextGenerationStreamResponse>(chunk)!);
        }

        // Assert
        Assert.Equal(2, chunks.Count);

        // First Chunk
        Assert.Equal(150, chunks[0].Index);
        Assert.Equal(1178, chunks[0].Token!.Id);
        Assert.Equal(" data", chunks[0].Token!.Text);
        Assert.Equal(-0.4560547, chunks[0].Token!.LogProb);
        Assert.False(chunks[0].Token!.Special);
        Assert.Equal("Write about the difference between Data Science and AI Engineering.\n\nData Science and AI Engineering are two interconnected fields that have gained immense popularity in recent years. While both fields deal with data and machine learning, they have distinct differences in terms of their focus, skills required, and applications.\n\nData Science is a multidisciplinary field that involves the extraction of insights and knowledge from large and complex data sets. It combines various disciplines such as mathematics, statistics, computer science, and domain expertise to analyze and interpret data. Data scientists use a variety of tools and techniques such as data cleaning, data wrangling, data visualization, and machine learning algorithms to derive insights and make informed decisions. They work closely with stakeholders to understand business requirements and translate them into data", chunks[0].GeneratedText);
        Assert.Null(chunks[0].Details);

        // Second Chunk
        Assert.Equal(149, chunks[1].Index);
        Assert.Equal(778, chunks[1].Token!.Id);
        Assert.Equal(" into", chunks[1].Token!.Text);
        Assert.Equal(-0.000011920929, chunks[1].Token!.LogProb);
        Assert.False(chunks[1].Token!.Special);
        Assert.Null(chunks[1].GeneratedText);
        Assert.Null(chunks[1].Details);
    }

    private static void WriteToStream(Stream stream, string input)
    {
        using var writer = new StreamWriter(stream, leaveOpen: true);
        writer.Write(input);
        writer.Flush();
        stream.Position = 0;
    }
}
