﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Embeddings;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Ollama;

public sealed class OllamaTextEmbeddingTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OllamaTextEmbeddingTests>()
        .Build();

    [Theory(Skip = "For manual verification only")]
    [InlineData("mxbai-embed-large", 1024)]
    [InlineData("nomic-embed-text", 768)]
    [InlineData("all-minilm", 384)]
    public async Task GenerateEmbeddingHasExpectedLengthForModelAsync(string modelId, int expectedVectorLength)
    {
        // Arrange
        const string TestInputString = "test sentence";

        OllamaConfiguration? config = this._configuration.GetSection("Ollama").Get<OllamaConfiguration>();
        Assert.NotNull(config);
        Assert.NotNull(config.Endpoint);

        var embeddingGenerator = new OllamaTextEmbeddingGenerationService(
            modelId,
            new Uri(config.Endpoint));

        // Act
        var result = await embeddingGenerator.GenerateEmbeddingAsync(TestInputString);

        // Assert
        Assert.Equal(expectedVectorLength, result.Length);
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("mxbai-embed-large", 1024)]
    [InlineData("nomic-embed-text", 768)]
    [InlineData("all-minilm", 384)]
    public async Task GenerateEmbeddingsHasExpectedResultsLengthForModelAsync(string modelId, int expectedVectorLength)
    {
        // Arrange
        string[] testInputStrings = ["test sentence 1", "test sentence 2", "test sentence 3"];

        OllamaConfiguration? config = this._configuration.GetSection("Ollama").Get<OllamaConfiguration>();
        Assert.NotNull(config);
        Assert.NotNull(config.Endpoint);

        var embeddingGenerator = new OllamaTextEmbeddingGenerationService(
            modelId,
            new Uri(config.Endpoint));

        // Act
        var result = await embeddingGenerator.GenerateEmbeddingsAsync(testInputStrings);

        // Assert
        Assert.Equal(testInputStrings.Length, result.Count);
        Assert.All(result, r => Assert.Equal(expectedVectorLength, r.Length));
    }
}
