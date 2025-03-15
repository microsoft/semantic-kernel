// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Core;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

/// <summary>
/// Unit tests for <see cref="HuggingFaceTextEmbeddingGenerationService"/> class.
/// </summary>
public sealed class HuggingFaceEmbeddingGenerationTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public HuggingFaceEmbeddingGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("embeddings_test_response_feature_extraction.json"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedModelShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGenerationService("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GenerateEmbeddingsAsync([]);

        //Assert
        Assert.EndsWith("/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGenerationService("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GenerateEmbeddingsAsync([]);

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
        var sut = new HuggingFaceTextEmbeddingGenerationService("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GenerateEmbeddingsAsync([]);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path");

        var sut = new HuggingFaceTextEmbeddingGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GenerateEmbeddingsAsync([]);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ModelUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGenerationService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        await sut.GenerateEmbeddingsAsync([]);

        //Assert
        Assert.Equal("https://fake-random-test-host/fake-path/pipeline/feature-extraction/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldSendDataToServiceAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGenerationService("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);
        List<string> data = ["test_string_1", "test_string_2"];

        //Act
        await sut.GenerateEmbeddingsAsync(data);

        //Assert
        var requestPayload = JsonSerializer.Deserialize<TextEmbeddingRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equivalent(data, requestPayload.Inputs);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGenerationService("fake-model", new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);

        //Act
        var embeddings = await sut.GenerateEmbeddingsAsync(["something"]);

        //Assert

        Assert.NotNull(embeddings);
        Assert.Single(embeddings);
        Assert.Equal(1024, embeddings.First().Length);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
