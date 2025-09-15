// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using SemanticKernel.Connectors.MistralAI.UnitTests;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="MistralAIEmbeddingGenerator"/>.
/// </summary>
public sealed class MistralAIEmbeddingGeneratorTests : MistralTestBase
{
    [Fact]
    public async Task ValidateGenerateAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsString("embeddings_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/embeddings", content);
        this.HttpClient = new System.Net.Http.HttpClient(this.DelegatingHandler, false);
        using var service = new MistralAIEmbeddingGenerator("mistral-small-latest", "key", httpClient: this.HttpClient);

        // Act
        List<string> data = ["Hello", "world"];
        var response = await service.GenerateAsync(data, default);

        // Assert
        Assert.NotNull(response);
        Assert.Equal(2, response.Count);
        Assert.Equal(1024, response[0].Vector.Length);
        Assert.Equal(1024, response[1].Vector.Length);
    }

    [Fact]
    public void ValidateGetService()
    {
        // Arrange
        using var service = new MistralAIEmbeddingGenerator("mistral-small-latest", "key");

        // Act & Assert
        Assert.Null(service.GetService(typeof(object), null));
        Assert.Same(service, service.GetService(typeof(MistralAIEmbeddingGenerator), service));
        Assert.IsType<EmbeddingGeneratorMetadata>(service.GetService(typeof(EmbeddingGeneratorMetadata), typeof(EmbeddingGeneratorMetadata)));
    }
}
