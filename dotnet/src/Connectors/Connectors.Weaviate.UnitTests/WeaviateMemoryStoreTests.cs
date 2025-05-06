// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Weaviate;

/// <summary>
/// Unit tests for <see cref="WeaviateMemoryStore"/> class.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public sealed class WeaviateMemoryStoreTests : IDisposable
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public WeaviateMemoryStoreTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();

        var getResponse = new
        {
            Properties = new Dictionary<string, string> {
                { "sk_id", "fake_id" },
                { "sk_description", "fake_description" },
                { "sk_text", "fake_text" },
                { "sk_additional_metadata", "fake_additional_metadata" }
            }
        };

        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(JsonSerializer.Serialize(getResponse, s_jsonSerializerOptions), Encoding.UTF8, MediaTypeNames.Application.Json);

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task NoAuthorizationHeaderShouldBeAddedIfApiKeyIsNotProvidedAsync()
    {
        //Arrange
        var sut = new WeaviateMemoryStore(this._httpClient, null, "https://fake-random-test-host/fake-path");

        //Act
        await sut.GetAsync("fake-collection", "fake-key");

        //Assert
        Assert.False(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));
    }

    [Fact]
    public async Task AuthorizationHeaderShouldBeAddedIfApiKeyIsProvidedAsync()
    {
        //Arrange
        var sut = new WeaviateMemoryStore(this._httpClient, "fake-api-key", "https://fake-random-test-host/fake-path");

        //Act
        await sut.GetAsync("fake-collection", "fake-key");

        //Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));

        var values = this._messageHandlerStub.RequestHeaders!.GetValues("Authorization");

        var value = values.SingleOrDefault();
        Assert.Equal("fake-api-key", value);
    }

    [Fact]
    public async Task ProvidedEndpointShouldBeUsedAsync()
    {
        //Arrange
        var sut = new WeaviateMemoryStore(this._httpClient, "fake-api-key", "https://fake-random-test-host/fake-path/");

        //Act
        await sut.GetAsync("fake-collection", "fake-key");

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path/");

        var sut = new WeaviateMemoryStore(this._httpClient, "fake-api-key");

        //Act
        await sut.GetAsync("fake-collection", "fake-key");

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
