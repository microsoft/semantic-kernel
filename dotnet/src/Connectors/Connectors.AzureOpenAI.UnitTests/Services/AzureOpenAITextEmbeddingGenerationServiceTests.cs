// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Moq;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="AzureOpenAITextEmbeddingGenerationService"/> class.
/// </summary>
public sealed class AzureOpenAITextEmbeddingGenerationServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AzureOpenAITextEmbeddingGenerationServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn = this.SuccessfulResponse;

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItCanBeCreatedWithApiKey(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItCanBeCreatedWithTokenCredential(bool includeLoggerFactory)
    {
        // Arrange & Act
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());

        var service = includeLoggerFactory ?
            new AzureOpenAITextEmbeddingGenerationService("deployment", "https://endpoint", credentials, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAITextEmbeddingGenerationService("deployment", "https://endpoint", credentials, "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItCanBeCreatedWithAzureOpenAIClient(bool includeLoggerFactory)
    {
        // Arrange & Act
        var client = new AzureOpenAIClient(new Uri("http://host"), "key");

        var service = includeLoggerFactory ?
            new AzureOpenAITextEmbeddingGenerationService("deployment", client, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAITextEmbeddingGenerationService("deployment", client, "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Fact]
    public async Task ItCanReturnEmptyResultWhenGenerateEmbeddingsForEmptyDataAsync()
    {
        // Arrange
        var service = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);

        // Act
        var result = await service.GenerateEmbeddingsAsync([]);

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public async Task ItShouldThrowExceptionWhenGenerateEmbeddingsWithEmptyResponseAsync()
    {
        // Arrange
        var service = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("""
            {
                "object": "list",
                "data": [],
                "model": "model-id"
            }
            """, Encoding.UTF8, "application/json")
        };

        // Act & Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => service.GenerateEmbeddingsAsync(["test"]));
        Assert.Equal("Expected 1 text embedding(s), but received 0", exception.Message);
    }

    [Fact]
    public async Task ItGeneratesEmbeddingsAsync()
    {
        // Arrange
        var service = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);

        // Act
        var result = await service.GenerateEmbeddingsAsync(["test"]);

        // Assert
        Assert.Single(result);

        var memory = result[0];

        Assert.Equal(0.018990106880664825, memory.Span[0]);
        Assert.Equal(-0.0073809814639389515, memory.Span[1]);
    }

    [Fact]
    public async Task ItGeneratesEmbeddingsWithDimensionsWorksAsync()
    {
        // Arrange
        var service = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient, dimensions: 256);

        // Act
        await service.GenerateEmbeddingsAsync(["test"]);

        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(requestContent);

        // Assert
        Assert.Equal(256, optionsJson.GetProperty("dimensions").GetInt32());
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    #region private

    private HttpResponseMessage SuccessfulResponse
        => new(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent("""
            {
                "object": "list",
                "data": [
                    {
                        "object": "embedding",
                        "embedding": "JJGbPCnc8bs=",
                        "index": 0
                    }
                ],
                "model": "model-id"
            }
            """, Encoding.UTF8, "application/json")
        };

    #endregion
}
