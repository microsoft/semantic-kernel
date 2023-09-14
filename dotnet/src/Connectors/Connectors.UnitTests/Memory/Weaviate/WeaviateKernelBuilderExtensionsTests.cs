// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.Weaviate;

public sealed class WeaviateKernelBuilderExtensionsTests : IDisposable
{
    private HttpMessageHandlerStub messageHandlerStub;
    private HttpClient httpClient;

    public WeaviateKernelBuilderExtensionsTests()
    {
        this.messageHandlerStub = new HttpMessageHandlerStub();

        this.httpClient = new HttpClient(this.messageHandlerStub, false);
    }

    [Theory]
    [InlineData(null, "https://fake-random-test-weaviate-host/v1/objects/fake-key")]
    [InlineData("v2", "https://fake-random-test-weaviate-host/v2/objects/fake-key")]
    public async Task WeaviateMemoryStoreShouldBeProperlyInitialized(string? apiVersion, string expectedAddress)
    {
        //Arrange
        var getResponse = new
        {
            Properties = new Dictionary<string, string> {
                { "sk_id", "fake_id" },
                { "sk_description", "fake_description" },
                { "sk_text", "fake_text" },
                { "sk_additional_metadata", "fake_additional_metadata" }
            }
        };

        this.messageHandlerStub.ResponseToReturn.Content = new StringContent(JsonSerializer.Serialize(getResponse, new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase }), Encoding.UTF8, MediaTypeNames.Application.Json);

        var builder = new KernelBuilder();
        builder.WithWeaviateMemoryStore(this.httpClient, "https://fake-random-test-weaviate-host", "fake-api-key", apiVersion);
        builder.WithAzureTextEmbeddingGenerationService("fake-deployment-name", "https://fake-random-test-host/fake-path", "fake -api-key");
        var kernel = builder.Build(); //This call triggers the internal factory registered by WithWeaviateMemoryStore method to create an instance of the WeaviateMemoryStore class.

        //Act
        await kernel.Memory.GetAsync("fake-collection", "fake-key"); //This call triggers a subsequent call to Weaviate memory store.

        //Assert
        Assert.Equal(expectedAddress, this.messageHandlerStub?.RequestUri?.AbsoluteUri);

        var headerValues = Enumerable.Empty<string>();
        var headerExists = this.messageHandlerStub?.RequestHeaders?.TryGetValues("Authorization", out headerValues);
        Assert.True(headerExists);
        Assert.Contains(headerValues!, (value) => value == "fake-api-key");
    }

    public void Dispose()
    {
        this.httpClient.Dispose();
        this.messageHandlerStub.Dispose();
    }
}
