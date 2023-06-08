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
    private HttpMessageHandlerStub messageHandlerStub;
    private HttpClient httpClient;

    public PineconeKernelBuilderExtensionsTests()
    {
        this.messageHandlerStub = new HttpMessageHandlerStub();

        this.httpClient = new HttpClient(this.messageHandlerStub, false);
    }

    [Fact]
    public async Task PineconeMemoryStoreShouldBeProperlyInitialized()
    {
        //Arrange
        this.messageHandlerStub.ResponseToReturn.Content = new StringContent("[\"fake-index1\"]", Encoding.UTF8, MediaTypeNames.Application.Json);

        var builder = new KernelBuilder();
        builder.WithPineconeMemoryStore("fake-environment", "fake-api-key", this.httpClient);
        builder.WithAzureTextEmbeddingGenerationService("fake-deployment-name", "https://fake-random-test-host/fake-path", "fake -api-key");
        var kernel = builder.Build(); //This call triggers the internal factory registered by WithPineconeMemoryStore method to create an instance of the PineconeMemoryStore class.

        //Act
        await kernel.Memory.GetCollectionsAsync(); //This call triggers a subsequent call to Pinecone memory store.

        //Assert
        Assert.Equal("https://controller.fake-environment.pinecone.io/databases", this.messageHandlerStub?.RequestUri?.AbsoluteUri);

        var headerValues = Enumerable.Empty<string>();
        var headerExists = this.messageHandlerStub?.RequestHeaders?.TryGetValues("Api-Key", out headerValues);
        Assert.True(headerExists);
        Assert.Contains(headerValues!, (value) => value == "fake-api-key");
    }

    public void Dispose()
    {
        this.httpClient.Dispose();
        this.messageHandlerStub.Dispose();
    }
}
