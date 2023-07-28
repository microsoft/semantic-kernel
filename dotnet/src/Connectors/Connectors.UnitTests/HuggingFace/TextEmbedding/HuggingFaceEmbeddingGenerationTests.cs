// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextEmbedding;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.HuggingFace.TextEmbedding;

/// <summary>
/// Unit tests for <see cref="HuggingFaceTextEmbeddingGeneration"/> class.
/// </summary>
public sealed class HuggingFaceEmbeddingGenerationTests : IDisposable
{
    private HttpMessageHandlerStub messageHandlerStub;
    private HttpClient httpClient;

    public HuggingFaceEmbeddingGenerationTests()
    {
        this.messageHandlerStub = new HttpMessageHandlerStub();
        this.messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("embeddings_test_response.json"));

        this.httpClient = new HttpClient(this.messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedModelShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGeneration("fake-model", this.httpClient, "https://fake-random-test-host/fake-path");

        //Act
        await sut.GenerateEmbeddingsAsync(new List<string>());

        //Assert
        Assert.EndsWith("/fake-model", this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGeneration("fake-model", this.httpClient, "https://fake-random-test-host/fake-path");

        //Act
        await sut.GenerateEmbeddingsAsync(new List<string>());

        //Assert
        Assert.True(this.messageHandlerStub.RequestHeaders?.Contains("User-Agent"));

        var values = this.messageHandlerStub.RequestHeaders!.GetValues("User-Agent");

        var value = values.SingleOrDefault();
        Assert.Equal("Semantic-Kernel", value);
    }

    [Fact]
    public async Task ProvidedEndpointShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGeneration("fake-model", this.httpClient, "https://fake-random-test-host/fake-path");

        //Act
        await sut.GenerateEmbeddingsAsync(new List<string>());

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this.httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path");

        var sut = new HuggingFaceTextEmbeddingGeneration("fake-model", this.httpClient);

        //Act
        await sut.GenerateEmbeddingsAsync(new List<string>());

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ModelUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGeneration("fake-model", this.httpClient, endpoint: "https://fake-random-test-host/fake-path");

        //Act
        await sut.GenerateEmbeddingsAsync(new List<string>());

        //Assert
        Assert.Equal("https://fake-random-test-host/fake-path/fake-model", this.messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldSendDataToServiceAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGeneration("fake-model", this.httpClient, "https://fake-random-test-host/fake-path");
        var data = new List<string>() { "test_string_1", "test_string_2", "test_string_3" };

        //Act
        await sut.GenerateEmbeddingsAsync(data);

        //Assert
        var requestPayload = JsonSerializer.Deserialize<TextEmbeddingRequest>(this.messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equivalent(data, requestPayload.Input);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextEmbeddingGeneration("fake-model", this.httpClient, "https://fake-random-test-host/fake-path");

        //Act
        var embeddings = await sut.GenerateEmbeddingsAsync(new List<string>());

        //Assert

        Assert.NotNull(embeddings);
        Assert.Equal(1, embeddings.Count);
        Assert.Equal(8, embeddings.First().Count);
    }

    public void Dispose()
    {
        this.httpClient.Dispose();
        this.messageHandlerStub.Dispose();
    }
}
