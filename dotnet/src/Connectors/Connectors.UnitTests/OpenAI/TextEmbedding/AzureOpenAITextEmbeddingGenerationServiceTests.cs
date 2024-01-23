// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.TextEmbedding;

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
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithApiKeyWorksCorrectly(bool includeLoggerFactory)
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
    public void ConstructorWithTokenCredentialWorksCorrectly(bool includeLoggerFactory)
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
    public void ConstructorWithOpenAIClientWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var client = new OpenAIClient("key");
        var service = includeLoggerFactory ?
            new AzureOpenAITextEmbeddingGenerationService("deployment", client, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAITextEmbeddingGenerationService("deployment", client, "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Fact]
    public async Task GenerateEmbeddingsForEmptyDataReturnsEmptyResultAsync()
    {
        // Arrange
        var service = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);

        // Act
        var result = await service.GenerateEmbeddingsAsync([]);

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public async Task GenerateEmbeddingsWithEmptyResponseThrowsExceptionAsync()
    {
        // Arrange
        var service = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(@"{
                                            ""object"": ""list"",
                                            ""data"": [],
                                            ""model"": ""model-id""
                                        }", Encoding.UTF8, "application/json")
        };

        // Act & Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => service.GenerateEmbeddingsAsync(["test"]));
        Assert.Equal("Text embedding not found", exception.Message);
    }

    [Fact]
    public async Task GenerateEmbeddingsByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(@"{
                                            ""object"": ""list"",
                                            ""data"": [
                                                {
                                                    ""object"": ""embedding"",
                                                    ""embedding"": [
                                                        0.018990106880664825,
                                                        -0.0073809814639389515
                                                    ],
                                                    ""index"": 0
                                                }
                                            ],
                                            ""model"": ""model-id""
                                        }", Encoding.UTF8, "application/json")
        };

        // Act
        var result = await service.GenerateEmbeddingsAsync(["test"]);

        // Assert
        Assert.Single(result);

        var memory = result[0];

        Assert.Equal(0.018990106880664825, memory.Span[0]);
        Assert.Equal(-0.0073809814639389515, memory.Span[1]);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
