// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Services;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="AzureOpenAITextEmbeddingGenerationService"/> class.
/// </summary>
public class AzureOpenAITextEmbeddingGenerationServiceTests
{
    [Fact]
    public void ItCanBeInstantiatedAndPropertiesSetAsExpected()
    {
        // Arrange
        var sut = new AzureOpenAITextEmbeddingGenerationService("deployment-name", "https://endpoint", "api-key", modelId: "model", dimensions: 2);
        var sutWithAzureOpenAIClient = new AzureOpenAITextEmbeddingGenerationService("deployment-name", new AzureOpenAIClient(new Uri("https://endpoint"), new ApiKeyCredential("apiKey")), modelId: "model", dimensions: 2);

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
}
