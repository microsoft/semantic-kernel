// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.ImageGeneration;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.HuggingFace.ImageGeneration;

/// <summary>
/// Unit tests for <see cref="HuggingFaceImageGeneration"/> class.
/// </summary>
public sealed class HuggingFaceImageGenerationTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public HuggingFaceImageGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StreamContent(HuggingFaceTestHelper.GetTestImageStreamResponse("image_response.png"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedModelShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageGeneration("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GenerateImageAsync("fake-text", 10, 10);

        //Assert
        Assert.EndsWith("/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task NoAuthorizationHeaderShouldBeAddedIfApiKeyIsNotProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageGeneration("fake-model", apiKey: null, httpClient: this._httpClient);

        //Act
        await sut.GenerateImageAsync("fake-text", 10, 10);

        //Assert
        Assert.False(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));
    }

    [Fact]
    public async Task AuthorizationHeaderShouldBeAddedIfApiKeyIsProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageGeneration("fake-model", apiKey: "fake-api-key", httpClient: this._httpClient);

        //Act
        await sut.GenerateImageAsync("fake-text", 10, 10);

        //Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));

        var values = this._messageHandlerStub.RequestHeaders!.GetValues("Authorization");

        var value = values.SingleOrDefault();
        Assert.Equal("Bearer fake-api-key", value);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageGeneration("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GenerateImageAsync("fake-text", 10, 10);

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
        var sut = new HuggingFaceImageGeneration("fake-model", endpoint: "https://fake-random-test-host/fake-path", httpClient: this._httpClient);

        //Act
        await sut.GenerateImageAsync("fake-text", 10, 10);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path");

        var sut = new HuggingFaceImageGeneration("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GenerateImageAsync("fake-text", 10, 10);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task DefaultAddressShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageGeneration("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GenerateImageAsync("fake-text", 10, 10);

        //Assert
        Assert.StartsWith("https://api-inference.huggingface.co/models", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ModelUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageGeneration("fake-model", endpoint: "https://fake-random-test-host/fake-path", httpClient: this._httpClient);

        //Act
        await sut.GenerateImageAsync("fake-text", 10, 10);

        //Assert
        Assert.Equal("https://fake-random-test-host/fake-path/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageGeneration("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GenerateImageAsync("fake-text", 10, 10);

        //Assert
        var requestPayload = JsonSerializer.Deserialize<TextToImageRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equal("fake-text", requestPayload.Input);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new HuggingFaceImageGeneration("fake-model", endpoint: "https://fake-random-test-host/fake-path", httpClient: this._httpClient);

        //Act
        var result = await sut.GenerateImageAsync("fake-text", 10, 10);

        //Assert
        Assert.NotNull(result);

        // TODO Add IImageResult abstraction
        //var completions = result.SingleOrDefault();
        //Assert.NotNull(completions);

        //var completion = await completions.GetCompletionAsync();
        //Assert.Equal("This is test completion response", completion);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
