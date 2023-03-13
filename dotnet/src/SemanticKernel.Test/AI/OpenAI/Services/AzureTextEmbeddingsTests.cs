// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.AI.OpenAI.Services.Deployments;
using Moq;
using Xunit;
using static Microsoft.SemanticKernel.AI.OpenAI.HttpSchema.EmbeddingResponse;

namespace SemanticKernelTests.AI.OpenAI.Services;
public class AzureTextEmbeddingsTests
{
    private readonly Mock<IAzureOpenAIServiceClient> _mockServiceClient;
    private readonly Mock<IAzureOpenAIDeploymentProvider> _mockDeploymentProvider;
    private readonly IList<EmbeddingResponseIndex> _embeddings;
    private readonly AzureTextEmbeddings _sut;

    public AzureTextEmbeddingsTests()
    {
        this._embeddings = new List<EmbeddingResponseIndex>();
        this._embeddings.Add(new EmbeddingResponseIndex { Index = 0, Values = new List<float>() { 1, 2 } });
        this._embeddings.Add(new EmbeddingResponseIndex { Index = 1, Values = new List<float>() { 3, 4 } });

        var embeddingResponse = new EmbeddingResponse() { Embeddings = this._embeddings };

        this._mockServiceClient = new Mock<IAzureOpenAIServiceClient>();
        this._mockServiceClient
            .Setup(sc => sc.CreateEmbeddingAsync(It.IsAny<EmbeddingRequest>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(embeddingResponse);

        this._mockDeploymentProvider = new Mock<IAzureOpenAIDeploymentProvider>();
        this._mockDeploymentProvider
            .Setup(p => p.GetDeploymentNameAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync("fake-deployment-name");

        this._sut = new AzureTextEmbeddings(this._mockServiceClient.Object, this._mockDeploymentProvider.Object, "fake-model-id");
    }

    [Fact]
    public async Task ItDelegatesDeploymentNameRetrievalToDeploymentProviderAsync()
    {
        //Arrange
        var data = new List<string>();

        //Act
        await this._sut.GenerateEmbeddingsAsync(data, CancellationToken.None);

        //Assert
        this._mockDeploymentProvider.Verify(p => p.GetDeploymentNameAsync("fake-model-id", It.IsAny<CancellationToken>()));
    }

    [Fact]
    public async Task ItDelegatesEmbeddingCreationToServiceClientAsync()
    {
        //Arrange
        var data = new List<string>() { "fake-text" };

        //Act
        await this._sut.GenerateEmbeddingsAsync(data, CancellationToken.None);

        //Assert
        this._mockServiceClient.Verify(sc => sc.CreateEmbeddingAsync(It.IsAny<EmbeddingRequest>(), "fake-deployment-name", It.IsAny<CancellationToken>()));
    }

    [Fact]
    public async Task ItCreatesEmbeddingPerDataElementAsync()
    {
        //Arrange
        var data = new List<string>() { "fake-text", "another-fake-text" };

        //Act
        var embeddings = await this._sut.GenerateEmbeddingsAsync(data, CancellationToken.None);

        //Assert
        this._mockServiceClient.Verify(sc => sc.CreateEmbeddingAsync(It.IsAny<EmbeddingRequest>(), "fake-deployment-name", It.IsAny<CancellationToken>()), Times.Exactly(2));
        Assert.Equal(4, embeddings.Count);
    }

    [Fact]
    public async Task ItConvertsEmbeddingResponseToEmbeddingsAsync()
    {
        //Arrange
        var data = new List<string>() { "fake-text" };

        //Act
        var embeddings = await this._sut.GenerateEmbeddingsAsync(data, CancellationToken.None);

        //Assert
        Assert.Equal(2, embeddings.Count);
        Assert.Equal(2, embeddings.ElementAt(0).Vector.Count());
        Assert.Equal(2, embeddings.ElementAt(1).Vector.Count());
    }
}
