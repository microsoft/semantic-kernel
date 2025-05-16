// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Google;

public sealed class EmbeddingGeneratorTests(ITestOutputHelper output) : TestsBase(output)
{
    private const string Input = "LLM is Large Language Model.";

    [RetryTheory(Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.GoogleAI)]
    [InlineData(ServiceType.VertexAI)]
    public async Task EmbeddingGeneratorAsync(ServiceType serviceType)
    {
        // Arrange
        using var sut = this.GetEmbeddingGenerator(serviceType);

        // Act
        var response = await sut.GenerateAsync(Input);

        // Assert
        this.Output.WriteLine($"Count of returned embeddings: {response.Vector.Length}");
        Assert.Equal(768, response.Vector.Length);
    }

    [RetryTheory(Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.GoogleAI)]
    public async Task EmbeddingGeneratorWithCustomDimensionsAsync(ServiceType serviceType)
    {
        // Arrange
        using var defaultService = this.GetEmbeddingGenerator(serviceType);
        var defaultResponse = await defaultService.GenerateAsync(Input);
        int defaultDimensions = defaultResponse.Vector.Length;

        // Insure custom dimensions are different from default
        int customDimensions = defaultDimensions == 512 ? 256 : 512;

        using var sut = this.GetEmbeddingGenerator(serviceType);

        // Act
        var response = await sut.GenerateAsync(Input);

        // Assert
        this.Output.WriteLine($"Default dimensions: {defaultDimensions}");
        this.Output.WriteLine($"Custom dimensions: {customDimensions}");
        this.Output.WriteLine($"Returned dimensions: {response.Vector.Length}");

        Assert.Equal(customDimensions, response.Vector.Length);
        Assert.NotEqual(defaultDimensions, response.Vector.Length);
    }
}
