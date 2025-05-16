// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Services;
using Moq;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="AzureOpenAITextEmbeddingGenerationService"/> class.
/// </summary>
[Obsolete("Temporary Tests for Obsolete AzureOpenAITextEmbeddingGenerationService")]
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
    public void ItCanBeInstantiatedAndPropertiesSetAsExpected(bool includeLoggerFactory)
    {
        // Arrange
        var sut = includeLoggerFactory ?
            new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", modelId: "model", dimensions: 2, loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", modelId: "model", dimensions: 2);
        var sutWithAzureOpenAIClient = new AzureOpenAITextEmbeddingGenerationService("deployment-name", new AzureOpenAIClient(new Uri("https://endpoint"), new ApiKeyCredential("apiKey")), modelId: "model", dimensions: 2, loggerFactory: this._mockLoggerFactory.Object);

        // Assert
        Assert.NotNull(sut);
        Assert.NotNull(sutWithAzureOpenAIClient);
        Assert.Equal("model", sut.Attributes[AIServiceExtensions.ModelIdKey]);
        Assert.Equal("model", sutWithAzureOpenAIClient.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public async Task ItGetEmbeddingsAsyncReturnsEmptyWhenProvidedDataIsEmpty()
    {
        // Arrange
        var sut = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key");

        // Act
        var result = await sut.GenerateEmbeddingsAsync([], null, CancellationToken.None);

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public async Task GetEmbeddingsAsyncReturnsEmptyWhenProvidedDataIsWhitespace()
    {
        // Arrange
        using HttpMessageHandlerStub handler = new()
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(File.ReadAllText("./TestData/text-embeddings-response.txt"))
            }
        };
        using HttpClient client = new(handler);

        var sut = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", httpClient: client);

        // Act
        var result = await sut.GenerateEmbeddingsAsync(["test"], null, CancellationToken.None);

        // Assert
        Assert.Single(result);
        Assert.Equal(4, result[0].Length);
    }

    [Fact]
    public async Task ItThrowsIfNumberOfResultsDiffersFromInputsAsync()
    {
        // Arrange
        using HttpMessageHandlerStub handler = new()
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(File.ReadAllText("./TestData/text-embeddings-multiple-response.txt"))
            }
        };
        using HttpClient client = new(handler);

        var sut = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", httpClient: client);

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(async () => await sut.GenerateEmbeddingsAsync(["test"], null, CancellationToken.None));
    }

    [Theory]
    [MemberData(nameof(Versions))]
    public async Task ItTargetsApiVersionAsExpected(string? apiVersion, string? expectedVersion = null)
    {
        // Arrange
        var sut = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", httpClient: this._httpClient, apiVersion: apiVersion);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-embeddings-response.txt"))
        };

        // Act
        await sut.GenerateEmbeddingsAsync(["test"], null, CancellationToken.None);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);

        Assert.Contains($"api-version={expectedVersion}", this._messageHandlerStub.RequestUri!.ToString());
    }

    public static TheoryData<string?, string?> Versions => new()
    {
        { "V2024_10_01_preview", "2024-10-01-preview" },
        { "V2024_10_01_PREVIEW", "2024-10-01-preview" },
        { "2024_10_01_Preview", "2024-10-01-preview" },
        { "2024-10-01-preview", "2024-10-01-preview" },
        { "V2024_08_01_preview", "2024-08-01-preview" },
        { "V2024_08_01_PREVIEW", "2024-08-01-preview" },
        { "2024_08_01_Preview", "2024-08-01-preview" },
        { "2024-08-01-preview", "2024-08-01-preview" },
        { "V2024_06_01", "2024-06-01" },
        { "2024_06_01", "2024-06-01" },
        { "2024-06-01", "2024-06-01" },
        { AzureOpenAIClientOptions.ServiceVersion.V2024_10_01_Preview.ToString(), null },
        { AzureOpenAIClientOptions.ServiceVersion.V2024_08_01_Preview.ToString(), null },
        { AzureOpenAIClientOptions.ServiceVersion.V2024_06_01.ToString(), null }
    };

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
