// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
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

    private VertexAIEmbeddingClient CreateEmbeddingsClient(
        string modelId = "fake-model",
        string? bearerKey = "fake-key")
    {
        var client = new VertexAIEmbeddingClient(
            httpClient: this._httpClient,
            modelId: modelId,
            bearerTokenProvider: () => ValueTask.FromResult(bearerKey ?? "fake-key"),
            apiVersion: VertexAIVersion.V1,
            location: "us-central1",
            projectId: "fake-project-id");
        return client;
    }

    private sealed class BearerTokenGenerator()
    {
        private int _index = 0;
        public required List<string> BearerKeys { get; init; }

        public ValueTask<string> GetBearerToken() => ValueTask.FromResult(this.BearerKeys[this._index++]);
    }
}
