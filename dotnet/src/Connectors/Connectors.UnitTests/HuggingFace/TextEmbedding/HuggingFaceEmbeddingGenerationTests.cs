// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextEmbedding;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.HuggingFace.TextEmbedding;

/// <summary>
/// Unit tests for <see cref="HuggingFaceTextEmbeddingGeneration"/> class.
/// </summary>
public class HuggingFaceEmbeddingGenerationTests : IDisposable
{
    private const string Endpoint = "http://localhost:5000/embeddings";
    private const string Model = "gpt2";

    private readonly HttpResponseMessage _response = new()
    {
        StatusCode = HttpStatusCode.OK,
    };

    /// <summary>
    /// Verifies that <see cref="HuggingFaceTextEmbeddingGeneration.GenerateEmbeddingsAsync"/>
    /// returns expected list of generated embeddings without errors.
    /// </summary>
    [Fact]
    public async Task ItReturnsEmbeddingsCorrectlyAsync()
    {
        // Arrange
        const int ExpectedEmbeddingCount = 1;
        const int ExpectedVectorCount = 8;
        List<string> data = new() { "test_string_1", "test_string_2", "test_string_3" };

        using var service = this.CreateService(HuggingFaceTestHelper.GetTestResponse("embeddings_test_response.json"));

        // Act
        var embeddings = await service.GenerateEmbeddingsAsync(data);

        // Assert
        Assert.NotNull(embeddings);
        Assert.Equal(ExpectedEmbeddingCount, embeddings.Count);
        Assert.Equal(ExpectedVectorCount, embeddings.First().Count);
    }

    /// <summary>
    /// Initializes <see cref="HuggingFaceTextEmbeddingGeneration"/> with mocked <see cref="HttpClientHandler"/>.
    /// </summary>
    /// <param name="testResponse">Test response for <see cref="HttpClientHandler"/> to return.</param>
    private HuggingFaceTextEmbeddingGeneration CreateService(string testResponse)
    {
        this._response.Content = new StringContent(testResponse);

        var httpClientHandler = HuggingFaceTestHelper.GetHttpClientHandlerMock(this._response);

        return new HuggingFaceTextEmbeddingGeneration(new Uri(Endpoint), Model, httpClientHandler);
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._response.Dispose();
        }
    }
}
