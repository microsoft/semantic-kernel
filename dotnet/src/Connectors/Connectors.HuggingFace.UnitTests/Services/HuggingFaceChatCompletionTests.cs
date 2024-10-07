// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Core;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

/// <summary>
/// Unit tests for <see cref="HuggingFaceChatCompletionTests"/> class.
/// </summary>
public sealed class HuggingFaceChatCompletionTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public HuggingFaceChatCompletionTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("chatcompletion_test_response.json"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false)
        {
            BaseAddress = new Uri("https://fake-random-test-host/fake-path")
        };
    }

    [Fact]
    public async Task ShouldContainModelInRequestBodyAsync()
    {
        //Arrange
        string modelId = "fake-model234";
        var sut = new HuggingFaceChatCompletionService(modelId, httpClient: this._httpClient);
        var chatHistory = CreateSampleChatHistory();

        //Act
        await sut.GetChatMessageContentAsync(chatHistory);

        //Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);

        Assert.Contains(modelId, requestContent, StringComparison.Ordinal);
    }

    [Fact]
    public async Task NoAuthorizationHeaderShouldBeAddedIfApiKeyIsNotProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceChatCompletionService("fake-model", apiKey: null, httpClient: this._httpClient);

        //Act
        await sut.GetChatMessageContentAsync("fake-text");

        //Assert
        Assert.False(this._messageHandlerStub.RequestHeaders?.Contains("Authorization"));
    }

    [Fact]
    public async Task AuthorizationHeaderShouldBeAddedIfApiKeyIsProvidedAsync()
    {
        //Arrange
        var sut = new HuggingFaceChatCompletionService("fake-model", apiKey: "fake-api-key", httpClient: this._httpClient);

        //Act
        await sut.GetChatMessageContentAsync("fake-text");

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
        var sut = new HuggingFaceChatCompletionService("fake-model", httpClient: this._httpClient);
        var chatHistory = CreateSampleChatHistory();

        //Act
        await sut.GetChatMessageContentAsync(chatHistory);

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
        var sut = new HuggingFaceChatCompletionService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);
        var chatHistory = CreateSampleChatHistory();

        //Act
        await sut.GetChatMessageContentAsync(chatHistory);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task HttpClientBaseAddressShouldBeUsedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = new Uri("https://fake-random-test-host/fake-path");

        var sut = new HuggingFaceChatCompletionService("fake-model", httpClient: this._httpClient);
        var chatHistory = CreateSampleChatHistory();

        //Act
        await sut.GetChatMessageContentAsync(chatHistory);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task DefaultAddressShouldBeUsedAsync()
    {
        this._httpClient.BaseAddress = null;
        //Arrange
        var sut = new HuggingFaceChatCompletionService("fake-model", httpClient: this._httpClient);
        var chatHistory = CreateSampleChatHistory();
        //Act
        await sut.GetChatMessageContentAsync(chatHistory);

        //Assert
        Assert.StartsWith("https://api-inference.huggingface.co/", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var sut = new HuggingFaceChatCompletionService("fake-model", httpClient: this._httpClient);
        var chatHistory = CreateSampleChatHistory();

        //Act
        await sut.GetChatMessageContentAsync(chatHistory);

        //Assert
        var requestPayload = JsonSerializer.Deserialize<ChatCompletionRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equal(chatHistory.Count, requestPayload.Messages!.Count);
        for (var i = 0; i < chatHistory.Count; i++)
        {
            Assert.Equal(chatHistory[i].Content, requestPayload.Messages[i].Content);
            Assert.Equal(chatHistory[i].Role.ToString(), requestPayload.Messages[i].Role);
        }
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new HuggingFaceChatCompletionService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);
        var chatHistory = CreateSampleChatHistory();

        //Act
        var contents = await sut.GetChatMessageContentsAsync(chatHistory);

        //Assert
        Assert.NotNull(contents);

        var content = contents.SingleOrDefault();
        Assert.NotNull(content);

        Assert.Equal("This is a testing chat completion response", content.Content);
    }

    [Fact]
    public async Task GetChatShouldHaveModelIdFromResponseAsync()
    {
        //Arrange
        var sut = new HuggingFaceChatCompletionService("fake-model", endpoint: new Uri("https://fake-random-test-host/fake-path"), httpClient: this._httpClient);
        var chatHistory = CreateSampleChatHistory();

        //Act
        var content = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(content.ModelId);
        Assert.Equal("teknium/OpenHermes-2.5-Mistral-7B", content.ModelId);
    }

    private static ChatHistory CreateSampleChatHistory()
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        return chatHistory;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
