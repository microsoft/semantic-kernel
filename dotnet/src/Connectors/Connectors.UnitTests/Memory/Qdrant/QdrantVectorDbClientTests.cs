// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.Qdrant;

public sealed class QdrantVectorDbClientTests : IDisposable
{
    private HttpMessageHandlerStub messageHandlerStub;
    private HttpClient httpClient;

    public QdrantVectorDbClientTests()
    {
        this.messageHandlerStub = new HttpMessageHandlerStub();

        this.httpClient = new HttpClient(this.messageHandlerStub, false);
    }

    [Fact]
    public async Task BaseAddressOfHttpClientShouldBeUsedIfNotOverrideProvided()
    {
        //Arrange
        this.httpClient.BaseAddress = new Uri("https://fake-random-test-host:123/fake-path/");

        var sut = new QdrantVectorDbClient(this.httpClient, 123);

        //Act
        await sut.DoesCollectionExistAsync("fake-collection");

        //Assert
        Assert.Equal("https://fake-random-test-host:123/fake-path/collections/fake-collection", this.messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task EndpointOverrideShouldBeUsedIfProvided()
    {
        //Arrange
        this.httpClient.BaseAddress = new Uri("https://fake-random-test-host:123/fake-path/");

        var sut = new QdrantVectorDbClient(this.httpClient, 123, "https://fake-random-test-host-override:123/");

        //Act
        await sut.DoesCollectionExistAsync("fake-collection");

        //Assert
        Assert.Equal("https://fake-random-test-host-override:123/collections/fake-collection", this.messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    public void Dispose()
    {
        this.httpClient.Dispose();
        this.messageHandlerStub.Dispose();
    }
}
