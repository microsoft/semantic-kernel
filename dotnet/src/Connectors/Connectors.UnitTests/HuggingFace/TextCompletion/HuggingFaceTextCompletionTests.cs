// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.HuggingFace.TextCompletion;

/// <summary>
/// Unit tests for <see cref="HuggingFaceTextCompletion"/> class.
/// </summary>
public sealed class HuggingFaceTextCompletionTests : IDisposable
{
    private HttpMessageHandlerStub messageHandlerStub;
    private HttpClient httpClient;

    public HuggingFaceTextCompletionTests()
    {
        this.messageHandlerStub = new HttpMessageHandlerStub();
        this.messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("completion_test_response.json"));

        this.httpClient = new HttpClient(this.messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedModelShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextCompletion("fake-model", httpClient: this.httpClient);

        //Act
        await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

        //Assert
        Assert.EndsWith("/fake-model", this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task NoAuthorizationHeaderShouldBeAddedIfApiKeyIsNotProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextCompletion("fake-model", apiKey: null, httpClient: this.httpClient);

        //Act
        await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

        //Assert
        Assert.False(this.messageHandlerStub.RequestHeaders?.Contains("Authorization"));
    }

    [Fact]
    public async Task AuthorizationHeaderShouldBeAddedIfApiKeyIsProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextCompletion("fake-model", apiKey: "fake-api-key", httpClient: this.httpClient);

        //Act
        await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

        //Assert
        Assert.True(this.messageHandlerStub.RequestHeaders?.Contains("Authorization"));

        var values = this.messageHandlerStub.RequestHeaders!.GetValues("Authorization");

        var value = values.SingleOrDefault();
        Assert.Equal("Bearer fake-api-key", value);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextCompletion("fake-model", httpClient: this.httpClient);

        //Act
        await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

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
        var sut = new HuggingFaceTextCompletion("fake-model", endpoint: "https://fake-random-test-host/fake-path", httpClient: this.httpClient);

        //Act
        await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this.httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path");

        var sut = new HuggingFaceTextCompletion("fake-model", httpClient: this.httpClient);

        //Act
        await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task DefaultAddressShouldBeUsedAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextCompletion("fake-model", httpClient: this.httpClient);

        //Act
        await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

        //Assert
        Assert.StartsWith("https://api-inference.huggingface.co/models", this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ModelUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextCompletion("fake-model", endpoint: "https://fake-random-test-host/fake-path", httpClient: this.httpClient);

        //Act
        await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

        //Assert
        Assert.Equal("https://fake-random-test-host/fake-path/fake-model", this.messageHandlerStub.RequestUri?.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextCompletion("fake-model", httpClient: this.httpClient);

        //Act
        await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

        //Assert
        var requestPayload = JsonSerializer.Deserialize<TextCompletionRequest>(this.messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equal("fake-text", requestPayload.Input);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new HuggingFaceTextCompletion("fake-model", endpoint: "https://fake-random-test-host/fake-path", httpClient: this.httpClient);

        //Act
        var result = await sut.GetCompletionsAsync("fake-text", new CompleteRequestSettings());

        //Assert
        Assert.NotNull(result);

        var completions = result.SingleOrDefault();
        Assert.NotNull(completions);

        var completion = await completions.GetCompletionAsync();
        Assert.Equal("This is test completion response", completion);
    }

    public void Dispose()
    {
        this.httpClient.Dispose();
        this.messageHandlerStub.Dispose();
    }
}
