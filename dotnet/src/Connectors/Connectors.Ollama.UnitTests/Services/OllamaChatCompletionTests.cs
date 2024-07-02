// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;
using OllamaSharp.Models.Chat;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests;

public sealed class OllamaChatCompletionTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public OllamaChatCompletionTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt"));
        this._httpClient = new HttpClient(this._messageHandlerStub, false) { BaseAddress = new Uri("http://localhost:11434") };
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        var sut = new OllamaChatCompletionService(
            "fake-model",
            new Uri("http://localhost:11434"),
            httpClient: this._httpClient);

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        //Act
        await sut.GetChatMessageContentsAsync(chat);

        //Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("User-Agent"));

        var values = this._messageHandlerStub.RequestHeaders!.GetValues("User-Agent");
        var value = values.SingleOrDefault();
        Assert.Equal("Semantic-Kernel", value);
    }

    [Fact]
    public async Task WhenHttpClientDoesNotHaveBaseAddresssProvidedEndpointShouldBeUsedAsync()
    {
        //Arrange
        this._httpClient.BaseAddress = null;
        var sut = new OllamaChatCompletionService("fake-model", new Uri("https://fake-random-test-host/fake-path/"), httpClient: this._httpClient);
        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        //Act
        await sut.GetChatMessageContentsAsync(chat);

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var sut = new OllamaChatCompletionService(
            "fake-model",
            new Uri("http://localhost:11434"),
            httpClient: this._httpClient);
        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        //Act
        await sut.GetChatMessageContentsAsync(chat);

        //Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.Equal("fake-text", requestPayload.Messages!.First().Content);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        var sut = new OllamaChatCompletionService(
            "fake-model",
            new Uri("http://localhost:11434"),
            httpClient: this._httpClient);

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        //Act
        var messages = await sut.GetChatMessageContentsAsync(chat);

        //Assert
        Assert.NotNull(messages);

        var message = messages.SingleOrDefault();
        Assert.NotNull(message);
        Assert.Equal("This is test completion response", message.Content);
    }

    [Fact]
    public async Task GetChatMessageContentsShouldHaveModelIdDefinedAsync()
    {
        //Arrange
        var sut = new OllamaChatCompletionService(
            "fake-model",
            new Uri("http://localhost:11434"),
            httpClient: this._httpClient);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt"))
        };

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        //Act
        var messages = await sut.GetChatMessageContentsAsync(chat);

        //Assert
        Assert.NotNull(messages);
        var message = messages.SingleOrDefault();
        Assert.NotNull(message);

        // Assert
        Assert.NotNull(message.ModelId);
        Assert.Equal("fake-model", message.ModelId);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsShouldHaveModelIdDefinedAsync()
    {
        //Arrange
        var expectedModel = "phi3";
        var sut = new OllamaChatCompletionService(
            expectedModel,
            new Uri("http://localhost:11434"),
            httpClient: this._httpClient);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StreamContent(File.OpenRead("TestData/chat_completion_test_response_stream.txt"))
        };

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        // Act
        StreamingChatMessageContent? lastMessage = null;
        await foreach (var message in sut.GetStreamingChatMessageContentsAsync(chat))
        {
            lastMessage = message;
        }

        // Assert
        Assert.NotNull(lastMessage!.ModelId);
        Assert.Equal(expectedModel, lastMessage.ModelId);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
