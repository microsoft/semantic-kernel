// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.VertexAI;

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

    private VertexAIEmbeddingClient CreateEmbeddingsClient(
        string modelId = "fake-model",
        string? bearerKey = "fake-key")
    {
        var client = new VertexAIEmbeddingClient(
            httpClient: this._httpClient,
            modelId: modelId,
            bearerKeyProvider: () => bearerKey ?? "fake-key",
            location: "us-central1",
            projectId: "fake-project-id");
        return client;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
