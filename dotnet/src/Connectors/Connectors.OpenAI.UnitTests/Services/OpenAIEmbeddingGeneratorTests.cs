// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="OpenAIEmbeddingGenerator"/> class.
/// </summary>
public sealed class OpenAIEmbeddingGeneratorTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public OpenAIEmbeddingGeneratorTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Fact]
    public void ItCanBeInstantiatedAndPropertiesSetAsExpected()
    {
        // Arrange
        using var sut = new OpenAIEmbeddingGenerator("model", "apiKey", dimensions: 2, loggerFactory: this._mockLoggerFactory.Object);
        using var sutWithOpenAIClient = new OpenAIEmbeddingGenerator("model", new OpenAIClient(new ApiKeyCredential("apiKey")), dimensions: 2, loggerFactory: this._mockLoggerFactory.Object);

        // Assert
        Assert.NotNull(sut);
        Assert.NotNull(sutWithOpenAIClient);

        Assert.Equal("model", sut.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelId);
        Assert.Equal(2, sut.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions);
        Assert.Equal("model", sutWithOpenAIClient.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelId);
        Assert.Equal(2, sutWithOpenAIClient.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelDimensions);
    }

    [Fact]
    public async Task ItGetEmbeddingsAsyncReturnsEmptyWhenProvidedDataIsEmpty()
    {
        // Arrange
        using var sut = new OpenAIEmbeddingGenerator("model", "apiKey");

        // Act
        var result = await sut.GenerateAsync([], null, CancellationToken.None);

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

        using var sut = new OpenAIEmbeddingGenerator("model", "apiKey", httpClient: client);

        // Act
        var result = await sut.GenerateAsync(["test"], null, CancellationToken.None);

        // Assert
        Assert.Single(result);
        Assert.Equal(4, result[0].Vector.Length);
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

        using var sut = new OpenAIEmbeddingGenerator("model", "apiKey", httpClient: client);

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(async () => await sut.GenerateAsync(["test"], null, CancellationToken.None));
    }

    [Fact]
    public async Task ItDoesNotIncludeDimensionsInRequestWhenNotProvided()
    {
        // Arrange
        using var sut = new OpenAIEmbeddingGenerator("model", "apiKey", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-embeddings-response.txt"))
        };

        // Act
        await sut.GenerateAsync(["test"], null, CancellationToken.None);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        var requestJson = JsonDocument.Parse(requestContent);

        // Verify dimensions is not in the request
        Assert.False(requestJson.RootElement.TryGetProperty("dimensions", out _));
    }

    [Fact]
    public async Task ItUsesDefaultDimensionsInRequestWhenProvidedInService()
    {
        // Arrange
        const int DefaultDimensions = 512;
        using var sut = new OpenAIEmbeddingGenerator(
            "model",
            "apiKey",
            dimensions: DefaultDimensions,
            httpClient: this._httpClient);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-embeddings-response.txt"))
        };

        // Act
        await sut.GenerateAsync(["test"], null, CancellationToken.None);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        var requestJson = JsonDocument.Parse(requestContent);

        // Verify dimensions is in the request with the default value
        Assert.True(requestJson.RootElement.TryGetProperty("dimensions", out var dimensionsElement));
        Assert.Equal(DefaultDimensions, dimensionsElement.GetInt32());
    }

    [Fact]
    public async Task ItUsesOptionsDimensionsInRequestInsteadOfDefault()
    {
        // Arrange
        const int DefaultDimensions = 512;
        const int OptionsDimensions = 256;

        using var sut = new OpenAIEmbeddingGenerator(
            "model",
            "apiKey",
            dimensions: DefaultDimensions,
            httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-embeddings-response.txt"))
        };

        var options = new EmbeddingGenerationOptions { Dimensions = OptionsDimensions };

        // Act
        await sut.GenerateAsync(["test"], options, CancellationToken.None);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        var requestJson = JsonDocument.Parse(requestContent);

        // Verify dimensions is in the request with the options value
        Assert.True(requestJson.RootElement.TryGetProperty("dimensions", out var dimensionsElement));
        Assert.Equal(OptionsDimensions, dimensionsElement.GetInt32());
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
