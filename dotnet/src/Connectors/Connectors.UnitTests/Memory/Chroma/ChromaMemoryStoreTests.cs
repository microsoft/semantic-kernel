// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.Chroma;

public sealed class ChromaMemoryStoreTests : IDisposable
{
    private HttpMessageHandlerStub messageHandlerStub;
    private HttpClient httpClient;

    public ChromaMemoryStoreTests()
    {
        this.messageHandlerStub = new HttpMessageHandlerStub();
        this.httpClient = this.GetHttpClientStub();
    }

    [Fact]
    public async Task ItUsesProvidedEndpointFromConstructorAsync()
    {
        // Arrange
        const string endpoint = "https://fake-random-test-host/fake-path/";
        var store = new ChromaMemoryStore(this.httpClient, endpoint);

        // Act
        await store.GetAsync("fake-collection", "fake-key");

        // Assert
        Assert.StartsWith(endpoint, this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItUsesBaseAddressFromHttpClientAsync()
    {
        // Arrange
        const string baseAddress = "https://fake-random-test-host/fake-path/";

        using var httpClient = this.GetHttpClientStub();
        httpClient.BaseAddress = new Uri(baseAddress);

        var store = new ChromaMemoryStore(httpClient);

        // Act
        await store.GetAsync("fake-collection", "fake-key");

        // Assert
        Assert.StartsWith(baseAddress, this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    public void Dispose()
    {
        this.httpClient.Dispose();
        this.messageHandlerStub.Dispose();
    }

    #region private ================================================================================

    private HttpClient GetHttpClientStub()
    {
        return new HttpClient(this.messageHandlerStub, false);
    }

    #endregion
}
