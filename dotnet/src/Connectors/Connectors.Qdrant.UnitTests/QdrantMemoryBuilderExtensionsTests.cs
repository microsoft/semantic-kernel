// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Qdrant.UnitTests;

[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public sealed class QdrantMemoryBuilderExtensionsTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public QdrantMemoryBuilderExtensionsTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task QdrantMemoryStoreShouldBeProperlyInitializedAsync()
    {
        // Arrange
        var embeddingGenerationMock = Mock.Of<ITextEmbeddingGenerationService>();

        this._httpClient.BaseAddress = new Uri("https://fake-random-qdrant-host");
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent("""{"result":{"collections":[]}}""", Encoding.UTF8, MediaTypeNames.Application.Json);

        var builder = new MemoryBuilder();
        builder.WithQdrantMemoryStore(this._httpClient, 123);
        builder.WithTextEmbeddingGeneration(embeddingGenerationMock);
        var memory = builder.Build(); //This call triggers the internal factory registered by WithQdrantMemoryStore method to create an instance of the QdrantMemoryStore class.

        // Act
        await memory.GetCollectionsAsync(); //This call triggers a subsequent call to Qdrant memory store.

        // Assert
        Assert.Equal("https://fake-random-qdrant-host/collections", this._messageHandlerStub?.RequestUri?.AbsoluteUri);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
