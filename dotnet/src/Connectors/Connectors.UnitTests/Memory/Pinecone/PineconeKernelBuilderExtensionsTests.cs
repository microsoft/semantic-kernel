// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.Pinecone;

public sealed class PineconeKernelBuilderExtensionsTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public PineconeKernelBuilderExtensionsTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task PineconeMemoryStoreShouldBeProperlyInitializedAsync()
    {
        //Arrange
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent("[\"fake-index1\"]", Encoding.UTF8, MediaTypeNames.Application.Json);

        var builder = new KernelBuilder();
        builder.WithPineconeMemoryStore("fake-environment", "fake-api-key", this._httpClient);
        builder.WithAzureTextEmbeddingGenerationService("fake-deployment-name", "https://fake-random-test-host/fake-path", "fake -api-key");
        var kernel = builder.Build(); //This call triggers the internal factory registered by WithPineconeMemoryStore method to create an instance of the PineconeMemoryStore class.

        //Act
        await kernel.Memory.GetCollectionsAsync(); //This call triggers a subsequent call to Pinecone memory store.

        //Assert
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
