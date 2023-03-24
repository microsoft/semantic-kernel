// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.HuggingFace.Services;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernelTests.AI.HuggingFace;

/// <summary>
/// Unit tests for <see cref="HuggingFaceBackend"/> class.
/// </summary>
public class HuggingFaceBackendTests : IDisposable
{
    private const string BaseUri = "http://localhost:5000";
    private const string Model = "gpt2";

    private readonly HttpResponseMessage _response = new()
    {
        StatusCode = HttpStatusCode.OK,
    };

    /// <summary>
    /// Verifies that <see cref="HuggingFaceBackend.CompleteAsync(string, CompleteRequestSettings)"/>
    /// returns expected completed text without errors.
    /// </summary>
    [Fact]
    public async Task ItReturnsCompletionCorrectlyAsync()
    {
        // Arrange
        const string prompt = "This is test";
        CompleteRequestSettings requestSettings = new();

        using var backend = this.CreateBackend(this.GetTestResponse("completion_test_response.json"));

        // Act
        var completion = await backend.CompleteAsync(prompt, requestSettings);

        // Assert
        Assert.Equal("This is test completion response", completion);
    }

    /// <summary>
    /// Verifies that <see cref="HuggingFaceBackend.GenerateEmbeddingsAsync(IList{string})"/>
    /// returns expected list of generated embeddings without errors.
    /// </summary>
    [Fact]
    public async Task ItReturnsEmbeddingsCorrectlyAsync()
    {
        // Arrange
        const int expectedEmbeddingCount = 1;
        const int expectedVectorCount = 8;
        List<string> data = new() { "test_string_1", "test_string_2", "test_string_3" };

        using var backend = this.CreateBackend(this.GetTestResponse("embeddings_test_response.json"));

        // Act
        var embeddings = await backend.GenerateEmbeddingsAsync(data);

        // Assert
        Assert.NotNull(embeddings);
        Assert.Equal(expectedEmbeddingCount, embeddings.Count);
        Assert.Equal(expectedVectorCount, embeddings.First().Count);
    }

    /// <summary>
    /// Reads test response from file for mocking purposes.
    /// </summary>
    /// <param name="fileName">Name of the file with test response.</param>
    private string GetTestResponse(string fileName)
    {
        return File.ReadAllText($"./AI/HuggingFace/TestData/{fileName}");
    }

    /// <summary>
    /// Initializes <see cref="HuggingFaceBackend"/> with mocked <see cref="HttpClientHandler"/>.
    /// </summary>
    /// <param name="testResponse">Test response for <see cref="HttpClientHandler"/> to return.</param>
    private HuggingFaceBackend CreateBackend(string testResponse)
    {
        var httpClientHandler = new Mock<HttpClientHandler>();

        this._response.Content = new StringContent(testResponse);

        httpClientHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>(
              "SendAsync",
              ItExpr.IsAny<HttpRequestMessage>(),
              ItExpr.IsAny<CancellationToken>())
           .ReturnsAsync(this._response);

        return new HuggingFaceBackend(BaseUri, Model, httpClientHandler.Object);
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
