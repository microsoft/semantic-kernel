// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Amazon;

public class BedrockTextEmbeddingTests
{
    [Theory(Skip = "For manual verification only")]
    [InlineData("amazon.titan-embed-text-v2:0")]
    [InlineData("amazon.titan-embed-text-v1")]
    [InlineData("cohere.embed-english-v3")]
    [InlineData("cohere.embed-multilingual-v3")]
    [Obsolete("Temporary Tests for Obsolete AzureOpenAITextEmbeddingGenerationService")]
    public async Task TextEmbeddingReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        List<string> prompts =
        [
            "The quick brown fox jumps over the lazy dog.",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "What is the capital of Spain?"
        ];
        var kernel = Kernel.CreateBuilder().AddBedrockTextEmbeddingGenerationService(modelId).Build();
        var textGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Act
        var response = await textGenerationService.GenerateEmbeddingsAsync(prompts).ConfigureAwait(true);

        // Assert
        Assert.NotNull(response);
        Assert.True(response.Count == prompts.Count);
        foreach (var embedding in response)
        {
            Assert.True(embedding.Length > 0);
        }
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("amazon.titan-embed-text-v2:0")]
    [InlineData("amazon.titan-embed-text-v1")]
    [InlineData("cohere.embed-english-v3")]
    [InlineData("cohere.embed-multilingual-v3")]
    public async Task EmbeddingGeneratorReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        List<string> prompts =
        [
            "The quick brown fox jumps over the lazy dog.",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "What is the capital of Spain?"
        ];
        var kernel = Kernel.CreateBuilder().AddBedrockEmbeddingGenerator(modelId).Build();
        var embeddingGenerator = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Act
        var response = await embeddingGenerator.GenerateAsync(prompts).ConfigureAwait(true);

        // Assert
        Assert.NotNull(response);
        Assert.True(response.Count == prompts.Count);
        foreach (var embedding in response)
        {
            Assert.True(embedding.Vector.Length > 0);
        }
    }
}
