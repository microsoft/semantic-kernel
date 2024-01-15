// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.VertexAI;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.VertexAI;
using SemanticKernel.UnitTests;
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
    public async Task ShouldReturnValidEmbeddingsResponseAsync()
    {
        // Arrange
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { EmbeddingModelId = "fake-model" };
        var client = this.CreateEmbeddingsClient(geminiConfiguration);
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

    private VertexAIEmbeddingsClient CreateEmbeddingsClient(GeminiConfiguration geminiConfiguration)
    {
        var client = new VertexAIEmbeddingsClient(
            httpClient: this._httpClient,
            embeddingModelId: geminiConfiguration.EmbeddingModelId!,
            httpRequestFactory: new VertexAIGeminiHttpRequestFactory(geminiConfiguration.ApiKey),
            endpointProvider: new VertexAIGeminiEndpointProvider(new VertexAIConfiguration("fake-loc", "fake-proj")));
        return client;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
