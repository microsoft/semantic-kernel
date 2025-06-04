// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.HuggingFace.EmbeddingGeneration;

public sealed class EmbeddingGenerationTests(ITestOutputHelper output) : HuggingFaceTestsBase(output)
{
    private const string FirstInput = "LLM is Large Language Model.";
    private const string SecondInput = "Semantic Kernel is an SDK that integrates Large Language Models (LLMs).";

    [Fact(Skip = "This test is for manual verification.")]
    [Obsolete("Temporary Tests for obsoleted ITextEmbeddingGenerationService interface")]
    public async Task TextEmbeddingGenerationWithSingleValueInputAsync()
    {
        // Arrange
        var sut = this.CreateEmbeddingService();

        // Act
        var response = await sut.GenerateEmbeddingAsync(FirstInput);

        // Assert
        this.Output.WriteLine($"Returned dimensions: {response.Length}");
        Assert.Equal(384, response.Length);
    }

    [Fact(Skip = "This test is for manual verification.")]
    [Obsolete("Temporary Tests for obsoleted ITextEmbeddingGenerationService interface")]
    public async Task TextEmbeddingGenerationWithMultipleValuesInputAsync()
    {
        // Arrange
        var sut = this.CreateEmbeddingService();

        // Act
        var response = await sut.GenerateEmbeddingsAsync([FirstInput, SecondInput]);

        // Assert
        this.Output.WriteLine($"Count of returned embeddings: {response.Count}");
        this.Output.WriteLine($"Returned dimensions for first input: {response[0].Length}");
        this.Output.WriteLine($"Returned dimensions for second input: {response[1].Length}");
        Assert.Equal(2, response.Count);
        Assert.Equal(384, response[0].Length);
        Assert.Equal(384, response[1].Length);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task EmbeddingGeneratorWithSingleValueInputAsync()
    {
        // Arrange
        using var sut = this.CreateEmbeddingGenerator();

        // Act
        var response = await sut.GenerateAsync(FirstInput);

        // Assert
        this.Output.WriteLine($"Returned dimensions: {response.Vector.Length}");
        Assert.Equal(1024, response.Vector.Length);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task EmbeddingGeneratorWithMultipleValuesInputAsync()
    {
        // Arrange
        using var sut = this.CreateEmbeddingGenerator();

        // Act
        var response = await sut.GenerateAsync([FirstInput, SecondInput]);

        // Assert
        this.Output.WriteLine($"Count of returned embeddings: {response.Count}");
        this.Output.WriteLine($"Returned dimensions for first input: {response[0].Vector.Length}");
        this.Output.WriteLine($"Returned dimensions for second input: {response[1].Vector.Length}");
        Assert.Equal(2, response.Count);
        Assert.Equal(1024, response[0].Vector.Length);
        Assert.Equal(1024, response[1].Vector.Length);
    }
}
