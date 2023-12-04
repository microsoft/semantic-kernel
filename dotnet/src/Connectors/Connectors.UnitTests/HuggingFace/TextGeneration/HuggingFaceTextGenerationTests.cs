// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.HuggingFace.TextGeneration;

/// <summary>
/// Unit tests for <see cref="HuggingFaceTextGenerationService"/> class.
/// </summary>
public sealed class HuggingFaceTextGenerationTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public HuggingFaceTextGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("completion_test_response.json"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedModelShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.EndsWith("/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task NoAuthorizationHeaderShouldBeAddedIfApiKeyIsNotProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", apiKey: null, httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.False(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));
    }

    [Fact]
    public async Task AuthorizationHeaderShouldBeAddedIfApiKeyIsProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", apiKey: "fake-api-key", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

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
        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

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
        var sut = new HuggingFaceTextGenerationService("fake-model", endpoint: "https://fake-random-test-host/fake-path", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path");

        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task DefaultAddressShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.StartsWith("https://api-inference.huggingface.co/models", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ModelUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", endpoint: "https://fake-random-test-host/fake-path", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        Assert.Equal("https://fake-random-test-host/fake-path/fake-model", this._messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", httpClient: this._httpClient);

        //Act
        await sut.GetTextContentsAsync("fake-text");

        //Assert
        var requestPayload = JsonSerializer.Deserialize<TextGenerationRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equal("fake-text", requestPayload.Input);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextGenerationService("fake-model", endpoint: "https://fake-random-test-host/fake-path", httpClient: this._httpClient);

        //Act
        var contents = await sut.GetTextContentsAsync("fake-test");

        //Assert
        Assert.NotNull(contents);

        var content = contents.SingleOrDefault();
        Assert.NotNull(content);

        Assert.Equal("This is test completion response", content);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
