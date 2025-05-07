// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Core;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

/// <summary>
/// Unit tests for <see cref="HuggingFaceEmbeddingGenerator"/> class.
/// </summary>
public sealed class HuggingFaceEmbeddingGeneratorTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public HuggingFaceEmbeddingGeneratorTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("embeddings_test_response_feature_extraction.json"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedModelShouldBeUsedAsync()
    {
        //Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GenerateAsync([]);

        //Assert
        Assert.EndsWith("/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GenerateAsync([]);

        //Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("User-Agent"));

        var values = this._messageHandlerStub.RequestHeaders!.GetValues("User-Agent");

        var value = values.SingleOrDefault();
        Assert.Equal("Semantic-Kernel", value);
    }

    [Fact]
    public async Task ProvidedEndpointShouldBeUsedAsync()
    {
        //Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GenerateAsync([]);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path");

        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GenerateAsync([]);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ModelUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GenerateAsync([]);

        //Assert
        Assert.Equal("https://fake-random-test-host/fake-path/pipeline/feature-extraction/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldSendDataToServiceAsync()
    {
        //Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);
        List<string> data = ["test_string_1", "test_string_2"];

        //Act
        await sut.GenerateAsync(data);

        //Assert
        var requestPayload = JsonSerializer.Deserialize<TextEmbeddingRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equivalent(data, requestPayload.Inputs);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        var result = await sut.GenerateAsync(["something"]);

        //Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(1024, result.First().Vector.Length);
    }

    [Fact]
    public void GetServiceShouldReturnNullWhenServiceKeyIsNull()
    {
        // Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        // Act
        var result = sut.GetService(typeof(object), null);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void GetServiceShouldReturnThisWhenServiceTypeIsInstanceOfGenerator()
    {
        // Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        // Act
        var result = sut.GetService(typeof(HuggingFaceEmbeddingGenerator), "serviceKey");

        // Assert
        Assert.Same(sut, result);
    }

    [Fact]
    public void GetServiceShouldReturnMetadataWhenServiceTypeIsEmbeddingGeneratorMetadata()
    {
        // Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        // Act
        var result = sut.GetService(typeof(EmbeddingGeneratorMetadata), "serviceKey");

        // Assert
        Assert.NotNull(result);
        Assert.IsType<EmbeddingGeneratorMetadata>(result);
        var metadata = (EmbeddingGeneratorMetadata)result;
        Assert.Equal("fake-model", metadata.DefaultModelId);
        Assert.Equal(new Uri("https://fake-random-test-host/fake-path"), metadata.ProviderUri);
    }

    [Fact]
    public void GetServiceShouldReturnNullWhenServiceTypeIsNotSupported()
    {
        // Arrange
        using var sut = new HuggingFaceEmbeddingGenerator("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        // Act
        var result = sut.GetService(typeof(string), "serviceKey");

        // Assert
        Assert.Null(result);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
