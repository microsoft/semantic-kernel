// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using OllamaSharp;
using OllamaSharp.Models.Chat;
using Xunit;
using ChatRole = Microsoft.Extensions.AI.ChatRole;

namespace SemanticKernel.Connectors.Ollama.UnitTests.Services;

public sealed class OllamaChatClientTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly MultipleHttpMessageHandlerStub _multiMessageHandlerStub;
    private readonly HttpResponseMessage _defaultResponseMessage;

    public OllamaChatClientTests()
    {
        this._defaultResponseMessage = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StreamContent(File.OpenRead("TestData/chat_completion_test_response.txt"))
        };

        this._multiMessageHandlerStub = new()
        {
            ResponsesToReturn = [this._defaultResponseMessage]
        };
        this._httpClient = new HttpClient(this._multiMessageHandlerStub, false) { BaseAddress = new Uri("http://localhost:11434") };
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        // Arrange
        using var ollamaClient = new OllamaApiClient(this._httpClient, "fake-model");
        var sut = (IChatClient)ollamaClient;
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "fake-text")
        };

        // Act
        await sut.GetResponseAsync(messages);

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
        Assert.NotNull(requestPayload);
        Assert.Equal("fake-text", requestPayload.Messages!.First().Content);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        // Arrange
        using var ollamaClient = new OllamaApiClient(this._httpClient, "fake-model");
        var sut = (IChatClient)ollamaClient;
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "fake-text")
        };

        // Act
        var response = await sut.GetResponseAsync(messages);

        // Assert
        Assert.NotNull(response);
        Assert.Equal("This is test completion response", response.Text);
    }

    [Fact]
    public async Task GetResponseShouldHaveModelIdAsync()
    {
        // Arrange
        var expectedModel = "llama3.2";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = (IChatClient)ollamaClient;
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "fake-text")
        };

        // Act
        var response = await sut.GetResponseAsync(messages);

        // Assert
        Assert.NotNull(response);

        // Verify the request was sent with the correct model
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
        Assert.NotNull(requestPayload);
        Assert.Equal(expectedModel, requestPayload.Model);
    }

    [Fact]
    public async Task GetStreamingResponseShouldWorkAsync()
    {
        // Arrange
        var expectedModel = "phi3";
        using var streamResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StreamContent(File.OpenRead("TestData/chat_completion_test_response_stream.txt"))
        };
        this._multiMessageHandlerStub.ResponsesToReturn = [streamResponse];

        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = (IChatClient)ollamaClient;
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "fake-text")
        };

        // Act
        var responseUpdates = new List<ChatResponseUpdate>();
        await foreach (var update in sut.GetStreamingResponseAsync(messages))
        {
            responseUpdates.Add(update);
        }

        // Assert
        Assert.NotEmpty(responseUpdates);
        var lastUpdate = responseUpdates.Last();
        Assert.NotNull(lastUpdate);

        // Verify the request was sent with the correct model
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
        Assert.NotNull(requestPayload);
        Assert.Equal(expectedModel, requestPayload.Model);
    }

    [Fact]
    public async Task GetResponseWithChatOptionsAsync()
    {
        // Arrange
        var expectedModel = "fake-model";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = (IChatClient)ollamaClient;
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "fake-text")
        };

        var chatOptions = new ChatOptions
        {
            Temperature = 0.5f,
            TopP = 0.9f,
            MaxOutputTokens = 100,
            StopSequences = ["stop me"]
        };

        // Act
        await sut.GetResponseAsync(messages, chatOptions);

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Equal(chatOptions.Temperature, requestPayload.Options.Temperature);
        Assert.Equal(chatOptions.TopP, requestPayload.Options.TopP);
        Assert.Equal(chatOptions.StopSequences, requestPayload.Options.Stop);
    }

    [Fact]
    public void GetServiceShouldReturnChatClientMetadata()
    {
        // Arrange
        var expectedModel = "llama3.2";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = (IChatClient)ollamaClient;

        // Act
        var metadata = sut.GetService(typeof(ChatClientMetadata));

        // Assert
        Assert.NotNull(metadata);
        Assert.IsType<ChatClientMetadata>(metadata);
        var chatMetadata = (ChatClientMetadata)metadata;
        Assert.Equal(expectedModel, chatMetadata.DefaultModelId);
    }

    [Fact]
    public async Task ShouldHandleCancellationTokenAsync()
    {
        // Arrange
        using var ollamaClient = new OllamaApiClient(this._httpClient, "fake-model");
        var sut = (IChatClient)ollamaClient;
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "fake-text")
        };

        using var cts = new CancellationTokenSource();
        cts.Cancel();

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(async () =>
            await sut.GetResponseAsync(messages, cancellationToken: cts.Token));
    }

    [Fact]
    public async Task ShouldWorkWithBuilderPatternAsync()
    {
        // Arrange
        using var ollamaClient = new OllamaApiClient(this._httpClient, "fake-model");
        IChatClient sut = ((IChatClient)ollamaClient).AsBuilder().Build();
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "fake-text")
        };

        // Act
        var response = await sut.GetResponseAsync(messages);

        // Assert
        Assert.NotNull(response);
        Assert.Equal("This is test completion response", response.Text);
    }

    [Fact]
    public void ShouldSupportDispose()
    {
        // Arrange
        using var sut = new OllamaApiClient(this._httpClient, "fake-model");

        // Act & Assert - Should not throw
        ((IChatClient)sut).Dispose();
    }

    [Fact]
    public async Task ShouldHandleMultipleMessagesAsync()
    {
        // Arrange
        using var ollamaClient = new OllamaApiClient(this._httpClient, "fake-model");
        IChatClient sut = ollamaClient;
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, "You are a helpful assistant."),
            new(ChatRole.User, "Hello"),
            new(ChatRole.Assistant, "Hi there!"),
            new(ChatRole.User, "How are you?")
        };

        // Act
        var response = await sut.GetResponseAsync(messages);

        // Assert
        Assert.NotNull(response);

        // Verify all messages were sent
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
        Assert.NotNull(requestPayload);
        Assert.Equal(4, requestPayload.Messages!.Count());
        var messagesList = requestPayload.Messages!.ToList();
        Assert.Equal("system", messagesList[0].Role);
        Assert.Equal("user", messagesList[1].Role);
        Assert.Equal("assistant", messagesList[2].Role);
        Assert.Equal("user", messagesList[3].Role);
    }

    public void Dispose()
    {
        this._httpClient?.Dispose();
        this._defaultResponseMessage?.Dispose();
        this._multiMessageHandlerStub?.Dispose();
    }
}
