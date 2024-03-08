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
        var client = this.CreateEmbeddingsClient(modelId: modelId);
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
        var client = this.CreateEmbeddingsClient();
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

    private GoogleAIEmbeddingClient CreateEmbeddingsClient(
        string modelId = "fake-model")
    {
        var client = new GoogleAIEmbeddingClient(
            httpClient: this._httpClient,
            embeddingModelId: modelId,
            apiKey: "fake-key");
        return client;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
