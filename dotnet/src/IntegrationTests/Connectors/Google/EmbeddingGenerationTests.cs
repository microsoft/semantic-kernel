// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Embeddings;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Google;

public sealed class EmbeddingGenerationTests(ITestOutputHelper output) : TestsBase(output)
{
    private const string Input = "LLM is Large Language Model.";

    [RetryTheory(Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.GoogleAI)]
    [InlineData(ServiceType.VertexAI)]
    public async Task EmbeddingGenerationAsync(ServiceType serviceType)
    {
        // Arrange
        var sut = this.GetEmbeddingService(serviceType);

        // Act
        var response = await sut.GenerateEmbeddingAsync(Input);

        // Assert
        this.Output.WriteLine($"Count of returned embeddings: {response.Length}");
        Assert.Equal(768, response.Length);
    }

    [RetryTheory(Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.GoogleAI)]
    public async Task EmbeddingGenerationWithCustomDimensionsAsync(ServiceType serviceType)
    {
        // Arrange
        var defaultService = this.GetEmbeddingService(serviceType);
        var defaultResponse = await defaultService.GenerateEmbeddingAsync(Input);
        int defaultDimensions = defaultResponse.Length;

        // Insure custom dimensions are different from default
        int customDimensions = defaultDimensions == 512 ? 256 : 512;

        var sut = this.GetEmbeddingServiceWithDimensions(serviceType, customDimensions);

        // Act
        var response = await sut.GenerateEmbeddingAsync(Input);

        // Assert
        this.Output.WriteLine($"Default dimensions: {defaultDimensions}");
        this.Output.WriteLine($"Custom dimensions: {customDimensions}");
        this.Output.WriteLine($"Returned dimensions: {response.Length}");

        Assert.Equal(customDimensions, response.Length);
        Assert.NotEqual(defaultDimensions, response.Length);
    }
}
