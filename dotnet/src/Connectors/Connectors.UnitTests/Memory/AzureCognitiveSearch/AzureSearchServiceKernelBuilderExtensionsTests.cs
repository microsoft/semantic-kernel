// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.AzureCognitiveSearch;

public sealed class AzureSearchServiceKernelBuilderExtensionsTests : IDisposable
{
    private HttpMessageHandlerStub messageHandlerStub;
    private HttpClient httpClient;

    public AzureSearchServiceKernelBuilderExtensionsTests()
    {
        this.messageHandlerStub = new HttpMessageHandlerStub();

        this.httpClient = new HttpClient(this.messageHandlerStub, false);
    }

    [Fact]
    public async Task AzureCognitiveSearchMemoryStoreShouldBeProperlyInitialized()
    {
        //Arrange
        this.messageHandlerStub.ResponseToReturn.Content = new StringContent("{\"value\": [{\"name\": \"fake-index1\"}]}", Encoding.UTF8, MediaTypeNames.Application.Json);

        var builder = new KernelBuilder();
        builder.WithAzureCognitiveSearchMemory("https://fake-random-test-host/fake-path", "fake-api-key", this.httpClient);
        builder.WithAzureTextEmbeddingGenerationService("fake-deployment-name", "https://fake-random-test-host/fake-path1", "fake -api-key");
        var kernel = builder.Build(); //This call triggers the internal factory registered by WithAzureAzureCognitiveSearchMemory method to create an instance of the AzureCognitiveSearchMemory class.

        //Act
        await kernel.Memory.GetCollectionsAsync(); //This call triggers a subsequent call to Azure Cognitive Search Memory store.

        //Assert
        Assert.Equal("https://fake-random-test-host/fake-path/indexes?$select=%2A&api-version=2021-04-30-Preview", this.messageHandlerStub?.RequestUri?.AbsoluteUri);

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
