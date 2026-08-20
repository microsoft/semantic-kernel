// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.VertexAI;

public sealed class VertexAIEmbeddingEndpointTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly List<IDisposable> _disposables = [];

    public VertexAIEmbeddingEndpointTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            """
            {
              "embedding": {
                "values": [0.1, 0.2, 0.3]
              }
            }
            """,
            Encoding.UTF8,
            "application/json");
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Theory]
    [InlineData("gemini-embedding-2", true)]
    [InlineData("gemini-embedding-2-preview", true)]
    [InlineData("gemini-embedding-2-0", true)]
    [InlineData("GEMINI-EMBEDDING-2", true)]
    [InlineData("gemini-embedding-001", false)]
    [InlineData("textembedding-gecko", false)]
    [InlineData("textembedding-gecko@003", false)]
    [InlineData("text-embedding-004", false)]
    [InlineData("custom-model", false)]
    public void UsesEmbedContentEndpoint_ReturnsExpectedValue(string modelId, bool expected)
    {
        Assert.Equal(expected, VertexAIEmbeddingClient.UsesEmbedContentEndpoint(modelId));
    }

    [Fact]
    public async Task GenerateEmbeddingsAsync_ForGeminiEmbedding2_SendsCorrectEmbedContentWireContractAsync()
    {
        // Arrange
        var client = this.CreateClient("gemini-embedding-2");
        const string InputText = "hello world";

        // Act
        var result = await client.GenerateEmbeddingsAsync([InputText]);

        // Assert - URI validation
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        string uri = this._messageHandlerStub.RequestUri.ToString();
        Assert.Contains(":embedContent", uri, StringComparison.Ordinal);
        Assert.DoesNotContain(":predict", uri, StringComparison.Ordinal);

        // Assert - Request wire payload validation
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        string requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"content\"", requestBody, StringComparison.Ordinal);
        Assert.Contains("\"parts\"", requestBody, StringComparison.Ordinal);
        Assert.Contains("\"text\":\"hello world\"", requestBody, StringComparison.Ordinal);
        Assert.DoesNotContain("\"instances\"", requestBody, StringComparison.Ordinal);
        Assert.DoesNotContain("\"predictions\"", requestBody, StringComparison.Ordinal);

        // Assert - Response parsing validation
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(new float[] { 0.1f, 0.2f, 0.3f }, result[0].ToArray());
    }

    [Fact]
    public async Task GenerateEmbeddingsAsync_ForLegacyModel_SendsCorrectPredictWireContractAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            """
            {
              "predictions": [
                {
                  "embeddings": {
                    "values": [0.4, 0.5, 0.6]
                  }
                }
              ]
            }
            """,
            Encoding.UTF8,
            "application/json");
        var client = this.CreateClient("text-embedding-004");
        const string InputText = "hello legacy";

        // Act
        var result = await client.GenerateEmbeddingsAsync([InputText]);

        // Assert - URI validation
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        string uri = this._messageHandlerStub.RequestUri.ToString();
        Assert.Contains(":predict", uri, StringComparison.Ordinal);
        Assert.DoesNotContain(":embedContent", uri, StringComparison.Ordinal);

        // Assert - Request wire payload validation
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        string requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"instances\"", requestBody, StringComparison.Ordinal);
        Assert.Contains("\"content\":\"hello legacy\"", requestBody, StringComparison.Ordinal);
        Assert.DoesNotContain("\"parts\"", requestBody, StringComparison.Ordinal);

        // Assert - Response parsing validation
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(new float[] { 0.4f, 0.5f, 0.6f }, result[0].ToArray());
    }

    [Fact]
    public async Task GenerateEmbeddingsAsync_ForGeminiEmbedding2_IncludesDimensionsInPayloadWhenProvidedAsync()
    {
        // Arrange
        var client = this.CreateClient("gemini-embedding-2", dimensions: 256);

        // Act
        await client.GenerateEmbeddingsAsync(["test with dimensions"]);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        string requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"outputDimensionality\":256", requestBody, StringComparison.Ordinal);
    }

    [Fact]
    public async Task GenerateEmbeddingsAsync_ForGeminiEmbedding2_OmitsDimensionsWhenNullAsync()
    {
        // Arrange
        var client = this.CreateClient("gemini-embedding-2", dimensions: null);

        // Act
        await client.GenerateEmbeddingsAsync(["test without dimensions"]);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        string requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.DoesNotContain("outputDimensionality", requestBody, StringComparison.Ordinal);
    }

    [Fact]
    public async Task GenerateEmbeddingsAsync_ForGeminiEmbedding2_IncludesTaskTypeAndTitleFromOptionsAsync()
    {
        // Arrange
        var client = this.CreateClient("gemini-embedding-2");
        var options = new EmbeddingGenerationOptions
        {
            AdditionalProperties = new AdditionalPropertiesDictionary
            {
                ["task_type"] = "RETRIEVAL_DOCUMENT",
                ["title"] = "Document Title"
            }
        };

        // Act
        await client.GenerateEmbeddingsAsync(["test with task_type and title"], options);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        string requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"taskType\":\"RETRIEVAL_DOCUMENT\"", requestBody, StringComparison.Ordinal);
        Assert.Contains("\"title\":\"Document Title\"", requestBody, StringComparison.Ordinal);
    }

    [Fact]
    public async Task GenerateEmbeddingsAsync_ForGeminiEmbedding2_MultipleInputs_SendsSequentialRequestsAndPreservesOrderAsync()
    {
        // Arrange
        var client = this.CreateClient("gemini-embedding-2");
        var response1 = this.TrackDisposable(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("""{"embedding": {"values": [1.0, 1.1]}}""", Encoding.UTF8, "application/json")
        });
        var response2 = this.TrackDisposable(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("""{"embedding": {"values": [2.0, 2.1]}}""", Encoding.UTF8, "application/json")
        });
        var response3 = this.TrackDisposable(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("""{"embedding": {"values": [3.0, 3.1]}}""", Encoding.UTF8, "application/json")
        });

        this._messageHandlerStub.ResponseQueue.Enqueue(response1);
        this._messageHandlerStub.ResponseQueue.Enqueue(response2);
        this._messageHandlerStub.ResponseQueue.Enqueue(response3);

        // Act
        var results = await client.GenerateEmbeddingsAsync(["text1", "text2", "text3"]);

        // Assert
        Assert.NotNull(results);
        Assert.Equal(3, results.Count);
        Assert.Equal(new float[] { 1.0f, 1.1f }, results[0].ToArray());
        Assert.Equal(new float[] { 2.0f, 2.1f }, results[1].ToArray());
        Assert.Equal(new float[] { 3.0f, 3.1f }, results[2].ToArray());
    }

    [Fact]
    public async Task GenerateEmbeddingsAsync_ForGeminiEmbedding2_PropagatesHttpExceptionOnFailureAsync()
    {
        // Arrange
        var client = this.CreateClient("gemini-embedding-2");
        this._messageHandlerStub.ResponseToReturn = this.TrackDisposable(new HttpResponseMessage(HttpStatusCode.InternalServerError)
        {
            Content = new StringContent("""{"error": "Internal server error"}""", Encoding.UTF8, "application/json")
        });

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(() =>
            client.GenerateEmbeddingsAsync(["test failing call"]));
    }

    [Fact]
    public async Task GenerateEmbeddingsAsync_ForGeminiEmbedding2_Cancellation_ThrowsOperationCanceledExceptionAsync()
    {
        // Arrange
        var client = this.CreateClient("gemini-embedding-2");
        using var cts = new CancellationTokenSource();
        cts.Cancel();

        // Act & Assert
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() =>
            client.GenerateEmbeddingsAsync(["test cancelled"], cancellationToken: cts.Token));
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
        foreach (var disposable in this._disposables)
        {
            disposable.Dispose();
        }
    }

    private T TrackDisposable<T>(T disposable) where T : IDisposable
    {
        this._disposables.Add(disposable);
        return disposable;
    }

    private VertexAIEmbeddingClient CreateClient(string modelId, int? dimensions = null)
    {
        return new VertexAIEmbeddingClient(
            httpClient: this._httpClient,
            modelId: modelId,
            bearerTokenProvider: () => ValueTask.FromResult("fake-key"),
            apiVersion: VertexAIVersion.V1,
            location: "us-central1",
            projectId: "fake-project-id",
            dimensions: dimensions);
    }
}
