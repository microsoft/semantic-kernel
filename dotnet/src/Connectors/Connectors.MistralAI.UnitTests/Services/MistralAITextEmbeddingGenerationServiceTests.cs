// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;

namespace SemanticKernel.Connectors.MistralAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="MistralAITextEmbeddingGenerationService"/>.
/// </summary>
[Obsolete("This class is deprecated and will be removed in a future release.")]
public sealed class MistralAITextEmbeddingGenerationServiceTests : MistralTestBase
{
    [Fact]
    public async Task ValidateGenerateEmbeddingsAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsString("embeddings_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/embeddings", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var service = new MistralAITextEmbeddingGenerationService("mistral-small-latest", "key", httpClient: this.HttpClient);

        // Act
        List<string> data = ["Hello", "world"];
        var response = await service.GenerateEmbeddingsAsync(data, default);

        // Assert
        Assert.NotNull(response);
        Assert.Equal(2, response.Count);
        Assert.Equal(1024, response[0].Length);
        Assert.Equal(1024, response[1].Length);
    }
}
