// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Moq;
using SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Fakes;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.VertexAI;

[SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope")]
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
    public async Task ShouldCallGetEndpointAsync()
    {
        // Arrange
        var endpointProviderMock = new Mock<IEndpointProvider>();
        endpointProviderMock.Setup(x => x.GetEmbeddingsEndpoint(It.IsAny<string>()))
            .Returns(new Uri("https://fake-endpoint.com/"));
        var sut = this.CreateEmbeddingsClient(endpointProvider: endpointProviderMock.Object);

        // Act
        await sut.GenerateEmbeddingsAsync(["text1", "text2"]);

        // Assert
        endpointProviderMock.VerifyAll();
    }

    [Fact]
    public async Task ShouldCallCreatePostRequestAsync()
    {
        // Arrange
        var requestFactoryMock = new Mock<IHttpRequestFactory>();
        requestFactoryMock.Setup(x => x.CreatePost(It.IsAny<object>(), It.IsAny<Uri>()))
            .Returns(new HttpRequestMessage(HttpMethod.Post, new Uri("https://fake-endpoint.com/")));
        var sut = this.CreateEmbeddingsClient(httpRequestFactory: requestFactoryMock.Object);

        // Act
        await sut.GenerateEmbeddingsAsync(["text1", "text2"]);

        // Assert
        requestFactoryMock.VerifyAll();
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

    private VertexAIEmbeddingClient CreateEmbeddingsClient(
        string modelId = "fake-model",
        string apiKey = "fake-api-key",
        IEndpointProvider? endpointProvider = null,
        IHttpRequestFactory? httpRequestFactory = null)
    {
        var client = new VertexAIEmbeddingClient(
            httpClient: this._httpClient,
            embeddingModelId: modelId,
            httpRequestFactory: httpRequestFactory ?? new FakeHttpRequestFactory(),
            endpointProvider: endpointProvider ?? new FakeEndpointProvider());
        return client;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
