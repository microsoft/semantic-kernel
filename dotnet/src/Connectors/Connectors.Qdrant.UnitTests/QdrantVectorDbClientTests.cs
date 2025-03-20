// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Xunit;

namespace SemanticKernel.Connectors.Qdrant.UnitTests;

[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public sealed class QdrantVectorDbClientTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public QdrantVectorDbClientTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task BaseAddressOfHttpClientShouldBeUsedIfNotOverrideProvidedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host:123/fake-path/");

        var sut = new QdrantVectorDbClient(this._httpClient, 123);

        //Act
        await sut.DoesCollectionExistAsync("fake-collection");

        //Assert
        Assert.Equal("https://fake-random-test-host:123/fake-path/collections/fake-collection", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task EndpointOverrideShouldBeUsedIfProvidedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host:123/fake-path/");

        var sut = new QdrantVectorDbClient(this._httpClient, 123, "https://fake-random-test-host-override:123/");

        //Act
        await sut.DoesCollectionExistAsync("fake-collection");

        //Assert
        Assert.Equal("https://fake-random-test-host-override:123/collections/fake-collection", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
