// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Moq;
using Xunit;
using static Microsoft.SemanticKernel.AI.OpenAI.HttpSchema.EmbeddingResponse;

namespace SemanticKernelTests.AI.OpenAI.Services;
public class OpenAITextEmbeddingsTests
{
    private readonly Mock<IOpenAIServiceClient> _mockServiceClient;
    private readonly IList<EmbeddingResponseIndex> _embeddings;
    private readonly OpenAITextEmbeddings _sut;

    public OpenAITextEmbeddingsTests()
    {
        this._embeddings = new List<EmbeddingResponseIndex>();
        this._embeddings.Add(new EmbeddingResponseIndex { Index = 0, Values = new List<float>() { 1, 2 } });
        this._embeddings.Add(new EmbeddingResponseIndex { Index = 1, Values = new List<float>() { 3, 4 } });

        var embeddingResponse = new EmbeddingResponse() { Embeddings = this._embeddings };

        this._mockServiceClient = new Mock<IOpenAIServiceClient>();
        this._mockServiceClient
            .Setup(sc => sc.CreateEmbeddingAsync(It.IsAny<OpenAIEmbeddingRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(embeddingResponse);

        this._sut = new OpenAITextEmbeddings(this._mockServiceClient.Object, "fake-model-id");
    }

    [Fact]
    public async Task ItDelegatesEmbeddingCreationToServiceClientAsync()
    {
        //Arrange
        var data = new List<string>() { "fake-text" };

        //Act
        await this._sut.GenerateEmbeddingsAsync(data, CancellationToken.None);

        //Assert
        this._mockServiceClient.Verify(sc => sc.CreateEmbeddingAsync(It.IsAny<OpenAIEmbeddingRequest>(), It.IsAny<CancellationToken>()));
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
