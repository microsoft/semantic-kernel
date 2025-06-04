// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;
using Moq;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="OpenAITextEmbeddingGenerationService"/> class.
/// </summary>
[Obsolete("Temporary tests for obsoleted OpenAITextEmbeddingGenerationService.")]
public class OpenAITextEmbeddingGenerationServiceTests
{
    [Fact]
    public void ItCanBeInstantiatedAndPropertiesSetAsExpected()
    {
        // Arrange
        var sut = new OpenAITextEmbeddingGenerationService("model", "apiKey", dimensions: 2);
        var sutWithOpenAIClient = new OpenAITextEmbeddingGenerationService("model", new OpenAIClient(new ApiKeyCredential("apiKey")), dimensions: 2);

        // Assert
        Assert.NotNull(sut);
        Assert.NotNull(sutWithOpenAIClient);
        Assert.Equal("model", sut.Attributes[AIServiceExtensions.ModelIdKey]);
        Assert.Equal("model", sutWithOpenAIClient.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItThrowsIfModelIdIsNotProvided()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => new OpenAITextEmbeddingGenerationService(" ", "apikey"));
        Assert.Throws<ArgumentException>(() => new OpenAITextEmbeddingGenerationService(" ", openAIClient: new(new ApiKeyCredential("apikey"))));
        Assert.Throws<ArgumentException>(() => new OpenAITextEmbeddingGenerationService("", "apikey"));
        Assert.Throws<ArgumentException>(() => new OpenAITextEmbeddingGenerationService("", openAIClient: new(new ApiKeyCredential("apikey"))));
        Assert.Throws<ArgumentNullException>(() => new OpenAITextEmbeddingGenerationService(null!, "apikey"));
        Assert.Throws<ArgumentNullException>(() => new OpenAITextEmbeddingGenerationService(null!, openAIClient: new(new ApiKeyCredential("apikey"))));
    }

    [Fact]
    public async Task ItGetEmbeddingsAsyncReturnsEmptyWhenProvidedDataIsEmpty()
    {
        // Arrange
        var sut = new OpenAITextEmbeddingGenerationService("model", "apikey");

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

        var sut = new OpenAITextEmbeddingGenerationService("model", "apikey", httpClient: client);

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

        var sut = new OpenAITextEmbeddingGenerationService("model", "apikey", httpClient: client);

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(async () => await sut.GenerateEmbeddingsAsync(["test"], null, CancellationToken.None));
    }

    [Fact]
    public async Task GetEmbeddingsDoesLogActionAsync()
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

        var modelId = "dall-e-2";
        var logger = new Mock<ILogger<OpenAITextEmbeddingGenerationService>>();
        logger.Setup(l => l.IsEnabled(It.IsAny<LogLevel>())).Returns(true);

        var mockLoggerFactory = new Mock<ILoggerFactory>();
        mockLoggerFactory.Setup(x => x.CreateLogger(It.IsAny<string>())).Returns(logger.Object);

        var sut = new OpenAITextEmbeddingGenerationService(modelId, "apiKey", httpClient: client, loggerFactory: mockLoggerFactory.Object);

        // Act
        await sut.GenerateEmbeddingsAsync(["description"]);

        // Assert
        logger.VerifyLog(LogLevel.Information, $"Action: {nameof(OpenAITextEmbeddingGenerationService.GenerateEmbeddingsAsync)}. OpenAI Model ID: {modelId}.", Times.Once());
    }
}
