// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using System.Linq;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Threading.Tasks;
using System;
using Xunit;
using Microsoft.SemanticKernel.Plugins.Memory;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone;
using Moq;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace SemanticKernel.Connectors.UnitTests.Memory.Pinecone;

public sealed class PineconeMemoryBuilderExtensionsTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public PineconeMemoryBuilderExtensionsTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task PineconeMemoryStoreShouldBeProperlyInitializedAsync()
    {
        // Arrange
        var embeddingGenerationMock = Mock.Of<ITextEmbeddingGeneration>();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent("[\"fake-index1\"]", Encoding.UTF8, MediaTypeNames.Application.Json);

        var builder = new MemoryBuilder();
        builder.WithPineconeMemoryStore("fake-environment", "fake-api-key", this._httpClient);
        builder.WithTextEmbeddingGeneration(embeddingGenerationMock);

        var memory = builder.Build(); //This call triggers the internal factory registered by WithPineconeMemoryStore method to create an instance of the PineconeMemoryStore class.

        // Act
        await memory.GetCollectionsAsync(); //This call triggers a subsequent call to Pinecone memory store.

        // Assert
        Assert.Equal("https://controller.fake-environment.pinecone.io/databases", this._messageHandlerStub?.RequestUri?.AbsoluteUri);

        var headerValues = Enumerable.Empty<string>();
        var headerExists = this._messageHandlerStub?.RequestHeaders?.TryGetValues("Api-Key", out headerValues);
        Assert.True(headerExists);
        Assert.Contains(headerValues!, (value) => value == "fake-api-key");
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
