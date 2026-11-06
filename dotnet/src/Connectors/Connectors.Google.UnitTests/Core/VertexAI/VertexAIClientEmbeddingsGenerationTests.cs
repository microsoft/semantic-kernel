// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.VertexAI;

public sealed class VertexAIClientEmbeddingsGenerationTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./TestData/vertex_embeddings_response.json";

    public VertexAIClientEmbeddingsGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(TestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldContainModelInRequestUriAsync()
    {
        // Arrange
        string modelId = "fake-model234";
        var client = this.CreateEmbeddingsClient(modelId: modelId);
        List<string> dataToEmbed =
        [
            "Write a story about a magic backpack.",
            "Print color of backpack."
        ];

        // Act
        await client.GenerateEmbeddingsAsync(dataToEmbed);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        Assert.Contains(modelId, this._messageHandlerStub.RequestUri.ToString(), StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldReturnValidEmbeddingsResponseAsync()
    {
        // Arrange
        var client = this.CreateEmbeddingsClient();
        var dataToEmbed = new List<string>()
        {
            "Write a story about a magic backpack.",
            "Print color of backpack."
        };

        // Act
        var embeddings = await client.GenerateEmbeddingsAsync(dataToEmbed);

        // Assert
        VertexAIEmbeddingResponse testDataResponse = JsonSerializer.Deserialize<VertexAIEmbeddingResponse>(
            await File.ReadAllTextAsync(TestDataFilePath))!;
        Assert.NotNull(embeddings);
        Assert.Collection(embeddings,
            values => Assert.Equal(testDataResponse.Predictions[0].Embeddings.Values, values),
            values => Assert.Equal(testDataResponse.Predictions[1].Embeddings.Values, values));
    }

    [Fact]
    public async Task ItCreatesPostRequestWithAuthorizationHeaderAsync()
    {
        // Arrange
        string bearerKey = "sample-key";
        var client = this.CreateEmbeddingsClient(bearerKey: bearerKey);
        IList<string> data = ["sample data"];

        // Act
        await client.GenerateEmbeddingsAsync(data);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.NotNull(this._messageHandlerStub.RequestHeaders.Authorization);
        Assert.Equal($"Bearer {bearerKey}", this._messageHandlerStub.RequestHeaders.Authorization.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestAsync()
    {
        // Arrange
        var client = this.CreateEmbeddingsClient();
        IList<string> data = ["sample data"];

        // Act
        await client.GenerateEmbeddingsAsync(data);

        // Assert
        Assert.Equal(HttpMethod.Post, this._messageHandlerStub.Method);
    }

    [Fact]
    public async Task ItCreatesPostRequestWithValidUserAgentAsync()
    {
        // Arrange
        var client = this.CreateEmbeddingsClient();
        IList<string> data = ["sample data"];

        // Act
        await client.GenerateEmbeddingsAsync(data);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, this._messageHandlerStub.RequestHeaders.UserAgent.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestWithSemanticKernelVersionHeaderAsync()
    {
        // Arrange
        var client = this.CreateEmbeddingsClient();
        IList<string> data = ["sample data"];
        var expectedVersion = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientBase));

        // Act
        await client.GenerateEmbeddingsAsync(data);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        var header = this._messageHandlerStub.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(expectedVersion, header);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    [Theory]
    [InlineData("https://malicious-site.com")]
    [InlineData("http://internal-network.local")]
    [InlineData("ftp://attacker.com")]
    [InlineData("//bypass.com")]
    [InlineData("javascript:alert(1)")]
    [InlineData("data:text/html,<script>alert(1)</script>")]
    public void ItThrowsOnLocationUrlInjectionAttempt(string maliciousLocation)
    {
        // Arrange
        var bearerTokenGenerator = new BearerTokenGenerator()
        {
            BearerKeys = ["key1", "key2", "key3"]
        };

        using var httpClient = new HttpClient();

        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
        {
            var client = new VertexAIEmbeddingClient(
                httpClient: httpClient,
                modelId: "fake-model",
                apiVersion: VertexAIVersion.V1,
                bearerTokenProvider: bearerTokenGenerator.GetBearerToken,
                location: maliciousLocation,
                projectId: "fake-project-id");
        });
    }

    [Theory]
    [InlineData("useast1")]
    [InlineData("us-east1")]
    [InlineData("europe-west4")]
    [InlineData("asia-northeast1")]
    [InlineData("us-central1-a")]
    [InlineData("northamerica-northeast1")]
    [InlineData("australia-southeast1")]
    [InlineData("global")]
    public void ItAcceptsValidHostnameSegments(string validLocation)
    {
        // Arrange
        var bearerTokenGenerator = new BearerTokenGenerator()
        {
            BearerKeys = ["key1", "key2", "key3"]
        };

        using var httpClient = new HttpClient();

        // Act & Assert
        var exception = Record.Exception(() =>
        {
            var client = new VertexAIEmbeddingClient(
                httpClient: httpClient,
                modelId: "fake-model",
                apiVersion: VertexAIVersion.V1,
                bearerTokenProvider: bearerTokenGenerator.GetBearerToken,
                location: validLocation,
                projectId: "fake-project-id");
        });

        Assert.Null(exception);
    }

    [Theory]
    [InlineData("gemini-embedding-2")]
    [InlineData("gemini-embedding-2-preview")]
    public async Task ShouldUseVertexEmbedContentContractAsync(string modelId)
    {
        var client = this.CreateEmbeddingsClient(modelId: modelId, location: "global");
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText("./TestData/vertex_embed_content_response.json"));

        var embeddings = await client.GenerateEmbeddingsAsync(["sample data"]);

        Assert.Equal($"https://aiplatform.googleapis.com/v1/projects/fake-project-id/locations/global/publishers/google/models/{modelId}:embedContent",
            this._messageHandlerStub.RequestUri!.ToString());
        using var body = JsonDocument.Parse(this._messageHandlerStub.RequestContent!);
        Assert.Equal("sample data", body.RootElement.GetProperty("content").GetProperty("parts")[0].GetProperty("text").GetString());
        Assert.False(body.RootElement.TryGetProperty("requests", out _));
        Assert.False(body.RootElement.TryGetProperty("instances", out _));
        Assert.False(body.RootElement.TryGetProperty("model", out _));
        Assert.Single(embeddings);
        Assert.Equal(new float[] { 0.1f, 0.2f, 0.3f }, embeddings[0].ToArray());
    }

    [Theory]
    [InlineData("text-embedding-004")]
    [InlineData("gemini-embedding-001")]
    public async Task ShouldUsePredictEndpointForLegacyEmbeddingModelAsync(string modelId)
    {
        var client = this.CreateEmbeddingsClient(modelId: modelId);

        await client.GenerateEmbeddingsAsync(["sample data"]);

        Assert.EndsWith(":predict", this._messageHandlerStub.RequestUri!.ToString(), StringComparison.Ordinal);
        using var body = JsonDocument.Parse(this._messageHandlerStub.RequestContent!);
        Assert.Equal(JsonValueKind.Array, body.RootElement.GetProperty("instances").ValueKind);
    }

    [Fact]
    public async Task ShouldEmbedEachInputSeparatelyAndPreserveOrderAsync()
    {
        using var handler = new MultipleHttpMessageHandlerStub();
        handler.AddJsonResponse("{\"embedding\":{\"values\":[0.1,0.2]}}");
        handler.AddJsonResponse("{\"embedding\":{\"values\":[0.3,0.4]}}");
        using var httpClient = handler.CreateHttpClient();
        var client = this.CreateEmbeddingsClient(modelId: "gemini-embedding-2", httpClient: httpClient);

        var embeddings = await client.GenerateEmbeddingsAsync(["first input", "second input"]);

        Assert.Equal(2, handler.RequestContents.Count);
        for (int i = 0; i < 2; i++)
        {
            using var body = JsonDocument.Parse(handler.RequestContents[i]!);
            Assert.Equal(i == 0 ? "first input" : "second input", body.RootElement.GetProperty("content").GetProperty("parts")[0].GetProperty("text").GetString());
        }

        Assert.Collection(embeddings,
            values => Assert.Equal(new float[] { 0.1f, 0.2f }, values.ToArray()),
            values => Assert.Equal(new float[] { 0.3f, 0.4f }, values.ToArray()));
    }

    [Theory]
    [InlineData(null, null, null)]
    [InlineData(1024, null, 1024)]
    [InlineData(null, 768, 768)]
    [InlineData(1024, 768, 768)]
    public async Task ShouldRespectEmbedContentDimensionsAsync(int? defaultDimensions, int? requestDimensions, int? expectedDimensions)
    {
        var client = this.CreateEmbeddingsClient(modelId: "gemini-embedding-2", dimensions: defaultDimensions);
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText("./TestData/vertex_embed_content_response.json"));

        await client.GenerateEmbeddingsAsync(["sample data"], new EmbeddingGenerationOptions { Dimensions = requestDimensions });

        using var body = JsonDocument.Parse(this._messageHandlerStub.RequestContent!);
        if (expectedDimensions.HasValue)
        {
            Assert.Equal(expectedDimensions.Value, body.RootElement.GetProperty("outputDimensionality").GetInt32());
        }
        else
        {
            Assert.False(body.RootElement.TryGetProperty("outputDimensionality", out _));
        }
    }

    [Fact]
    public async Task ShouldCancelBeforeSendingEmbedContentAsync()
    {
        var client = this.CreateEmbeddingsClient(modelId: "gemini-embedding-2");
        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();

        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => client.GenerateEmbeddingsAsync(["sample data"], cancellationToken: cancellation.Token));

        Assert.Null(this._messageHandlerStub.RequestUri);
    }

    [Fact]
    public async Task ShouldStopEmbedContentBatchAfterHttpFailureAsync()
    {
        using var handler = new MultipleHttpMessageHandlerStub();
        handler.AddJsonResponse("{\"embedding\":{\"values\":[0.1,0.2]}}");
        handler.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.BadRequest));
        using var httpClient = handler.CreateHttpClient();
        var client = this.CreateEmbeddingsClient(modelId: "gemini-embedding-2", httpClient: httpClient);

        await Assert.ThrowsAsync<Microsoft.SemanticKernel.HttpOperationException>(() => client.GenerateEmbeddingsAsync(["first", "second", "third"]));

        Assert.Equal(2, handler.RequestContents.Count);
    }

    [Fact]
    public async Task ShouldUseGlobalEndpointWhenLocationIsGlobalAsync()
    {
        // Arrange
        var client = new VertexAIEmbeddingClient(
            httpClient: this._httpClient,
            modelId: "fake-model",
            bearerTokenProvider: () => ValueTask.FromResult("fake-key"),
            apiVersion: VertexAIVersion.V1,
            location: "global",
            projectId: "fake-project-id");
        IList<string> data = ["sample data"];

        // Act
        await client.GenerateEmbeddingsAsync(data);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        var requestUri = this._messageHandlerStub.RequestUri.ToString();
        Assert.StartsWith("https://aiplatform.googleapis.com/", requestUri);
        Assert.Contains("/locations/global/", requestUri, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldUseRegionalEndpointWhenLocationIsRegionalAsync()
    {
        // Arrange
        var client = new VertexAIEmbeddingClient(
            httpClient: this._httpClient,
            modelId: "fake-model",
            bearerTokenProvider: () => ValueTask.FromResult("fake-key"),
            apiVersion: VertexAIVersion.V1,
            location: "us-central1",
            projectId: "fake-project-id");
        IList<string> data = ["sample data"];

        // Act
        await client.GenerateEmbeddingsAsync(data);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        var requestUri = this._messageHandlerStub.RequestUri.ToString();
        Assert.StartsWith("https://us-central1-aiplatform.googleapis.com/", requestUri);
        Assert.Contains("/locations/us-central1/", requestUri, StringComparison.Ordinal);
    }

    private VertexAIEmbeddingClient CreateEmbeddingsClient(
        string modelId = "fake-model",
        string? bearerKey = "fake-key",
        HttpClient? httpClient = null,
        int? dimensions = null,
        string location = "us-central1")
    {
        var client = new VertexAIEmbeddingClient(
            httpClient: httpClient ?? this._httpClient,
            modelId: modelId,
            bearerTokenProvider: () => ValueTask.FromResult(bearerKey ?? "fake-key"),
            apiVersion: VertexAIVersion.V1,
            location: location,
            projectId: "fake-project-id",
            dimensions: dimensions);
        return client;
    }

    private sealed class BearerTokenGenerator()
    {
        private int _index = 0;
        public required List<string> BearerKeys { get; init; }

        public ValueTask<string> GetBearerToken() => ValueTask.FromResult(this.BearerKeys[this._index++]);
    }
}
