// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;
using OllamaSharp;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Ollama;

[Obsolete("Temporary tests for the obsolete ITextEmbeddingGenerationService.")]
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

        using var ollamaClient = new OllamaApiClient(
            uriString: config.Endpoint,
            defaultModel: modelId);

        var embeddingGenerator = ollamaClient.AsEmbeddingGenerationService();

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

        using var ollamaClient = new OllamaApiClient(
            uriString: config.Endpoint,
            defaultModel: modelId);

        var chatService = ollamaClient.AsChatCompletionService();
        var embeddingGenerator = ollamaClient.AsEmbeddingGenerationService();

        // Act
        var result = await embeddingGenerator.GenerateEmbeddingsAsync(testInputStrings);

        // Assert
        Assert.Equal(testInputStrings.Length, result.Count);
        Assert.All(result, r => Assert.Equal(expectedVectorLength, r.Length));
    }
}
