// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.GoogleAI;

public sealed class GoogleAIClientEmbeddingsGenerationTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./TestData/embeddings_response.json";

    public GoogleAIClientEmbeddingsGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(TestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldSendModelIdInEachEmbeddingRequestAsync()
    {
        // Arrange
        string modelId = "fake-model";
        string apiKey = "fake-api-key";
        var client = this.CreateEmbeddingsClient(modelId, apiKey);
        var dataToEmbed = new List<string>()
        {
            "Write a story about a magic backpack.",
            "Print color of backpack."
        };

        // Act
        await client.GenerateEmbeddingsAsync(dataToEmbed);

        // Assert
        var request = JsonSerializer.Deserialize<GoogleAIEmbeddingRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Collection(request.Requests,
            item => Assert.Contains(modelId, item.Model, StringComparison.Ordinal),
            item => Assert.Contains(modelId, item.Model, StringComparison.Ordinal));
    }

    [Fact]
    public async Task ShouldReturnValidEmbeddingsResponseAsync()
    {
        // Arrange
        string modelId = "fake-model";
        string apiKey = "fake-api-key";
        var client = this.CreateEmbeddingsClient(modelId, apiKey);
        var dataToEmbed = new List<string>()
        {
            "Write a story about a magic backpack.",
            "Print color of backpack."
        };

        // Act
        var embeddings = await client.GenerateEmbeddingsAsync(dataToEmbed);

        // Assert
        GoogleAIEmbeddingResponse testDataResponse = JsonSerializer.Deserialize<GoogleAIEmbeddingResponse>(
            await File.ReadAllTextAsync(TestDataFilePath))!;
        Assert.NotNull(embeddings);
        Assert.Collection(embeddings,
            values => Assert.Equal(testDataResponse.Embeddings[0].Values, values),
            values => Assert.Equal(testDataResponse.Embeddings[1].Values, values));
    }

    private GoogleAIEmbeddingsClient CreateEmbeddingsClient(string modelId, string apiKey)
    {
        var client = new GoogleAIEmbeddingsClient(
            httpClient: this._httpClient,
            embeddingModelId: modelId,
            httpRequestFactory: new GoogleAIGeminiHttpRequestFactory(),
            endpointProvider: new GoogleAIGeminiEndpointProvider(apiKey));
        return client;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
