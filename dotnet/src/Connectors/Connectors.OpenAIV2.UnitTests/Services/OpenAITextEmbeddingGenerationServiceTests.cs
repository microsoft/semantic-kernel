// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;
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
    public async Task IGetEmbeddingsAsyncReturnsEmptyWhenProvidedDataIsWhitespace()
    {
        using HttpMessageHandlerStub handler = new()
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(File.ReadAllText("./TestData/text-embeddings-response.txt"))
            }
        };
        using HttpClient client = new(handler);

        // Arrange
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
        using HttpMessageHandlerStub handler = new()
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(File.ReadAllText("./TestData/text-embeddings-multiple-response.txt"))
            }
        };
        using HttpClient client = new(handler);

        // Arrange
        var sut = new OpenAITextEmbeddingGenerationService("model", "apikey", httpClient: client);

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(async () => await sut.GenerateEmbeddingsAsync(["test"], null, CancellationToken.None));
    }
}
