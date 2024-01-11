#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini.GoogleAI;
using SemanticKernel.UnitTests;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini.GoogleAI;

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
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { EmbeddingModelId = "fake-model" };
        var client = this.CreateEmbeddingsClient(geminiConfiguration);
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
            item => Assert.Contains(geminiConfiguration.EmbeddingModelId, item.Model, StringComparison.Ordinal),
            item => Assert.Contains(geminiConfiguration.EmbeddingModelId, item.Model, StringComparison.Ordinal));
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
        GoogleAIEmbeddingResponse testDataResponse = JsonSerializer.Deserialize<GoogleAIEmbeddingResponse>(
            await File.ReadAllTextAsync(TestDataFilePath))!;
        Assert.NotNull(embeddings);
        Assert.Collection(embeddings,
            values => Assert.Equal(testDataResponse.Embeddings[0].Values, values),
            values => Assert.Equal(testDataResponse.Embeddings[1].Values, values));
    }

    private GoogleAIEmbeddingsClient CreateEmbeddingsClient(GeminiConfiguration geminiConfiguration)
    {
        var client = new GoogleAIEmbeddingsClient(
            httpClient: this._httpClient,
            configuration: geminiConfiguration,
            httpRequestFactory: new GoogleAIGeminiHttpRequestFactory(),
            endpointProvider: new GoogleAIGeminiEndpointProvider(geminiConfiguration.ApiKey));
        return client;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
