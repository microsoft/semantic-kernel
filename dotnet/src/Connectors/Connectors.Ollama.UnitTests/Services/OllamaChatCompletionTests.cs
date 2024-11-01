// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;
using OllamaSharp;
using OllamaSharp.Models.Chat;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests.Services;

public sealed class OllamaChatCompletionTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public OllamaChatCompletionTests()
    {
        this._messageHandlerStub = new()
        {
            ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StreamContent(File.OpenRead("TestData/chat_completion_test_response_stream.txt"))
            }
        };
        this._httpClient = new HttpClient(this._messageHandlerStub, false) { BaseAddress = new Uri("http://localhost:11434") };
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        using var ollamaClient = new OllamaApiClient(this._httpClient, "fake-model");
        var sut = ollamaClient.AsChatCompletionService();
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
        using var ollamaClient = new OllamaApiClient(this._httpClient, "fake-model");
        var sut = ollamaClient.AsChatCompletionService();

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
    public async Task GetChatMessageContentsShouldHaveModelAndInnerContentAsync()
    {
        //Arrange
        using var ollamaClient = new OllamaApiClient(this._httpClient, "phi3");
        var sut = ollamaClient.AsChatCompletionService();

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        //Act
        var messages = await sut.GetChatMessageContentsAsync(chat);

        //Assert
        Assert.NotNull(messages);
        var message = messages.SingleOrDefault();
        Assert.NotNull(message);

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Null(requestPayload.Options.Stop);
        Assert.Null(requestPayload.Options.Temperature);
        Assert.Null(requestPayload.Options.TopK);
        Assert.Null(requestPayload.Options.TopP);

        Assert.NotNull(message.ModelId);
        Assert.Equal("phi3", message.ModelId);

        // Ollama Sharp always perform streaming even for non-streaming calls,
        // The inner content in this case is the full list of chunks returned by the Ollama Client.
        Assert.NotNull(message.InnerContent);
        Assert.IsType<ChatDoneResponseStream>(message.InnerContent);
        var doneStream = message.InnerContent as ChatDoneResponseStream;
        Assert.NotNull(doneStream);
        Assert.True(doneStream.Done);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsShouldHaveModelAndInnerContentAsync()
    {
        //Arrange
        var expectedModel = "phi3";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = ollamaClient.AsChatCompletionService();

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        // Act
        StreamingChatMessageContent? lastMessage = null;
        await foreach (var message in sut.GetStreamingChatMessageContentsAsync(chat))
        {
            lastMessage = message;
            Assert.NotNull(message.InnerContent);
        }

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Null(requestPayload.Options.Stop);
        Assert.Null(requestPayload.Options.Temperature);
        Assert.Null(requestPayload.Options.TopK);
        Assert.Null(requestPayload.Options.TopP);

        // Assert.NotNull(lastMessage!.ModelId);
        // Assert.Equal(expectedModel, lastMessage.ModelId);
        // Add back once this bugfix is merged
        // https://github.com/awaescher/OllamaSharp/pull/128

        Assert.IsType<ChatDoneResponseStream>(lastMessage.InnerContent);
        var innerContent = lastMessage.InnerContent as ChatDoneResponseStream;
        Assert.NotNull(innerContent);
        Assert.True(innerContent.Done);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsShouldHaveDoneReasonAsync()
    {
        //Arrange
        var expectedModel = "phi3";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = ollamaClient.AsChatCompletionService();

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        // Act
        StreamingChatMessageContent? lastMessage = null;
        await foreach (var message in sut.GetStreamingChatMessageContentsAsync(chat))
        {
            lastMessage = message;
        }

        // Assert
        Assert.NotNull(lastMessage);
        Assert.IsType<ChatDoneResponseStream>(lastMessage.InnerContent);
        var innerContent = lastMessage.InnerContent as ChatDoneResponseStream;
        Assert.NotNull(innerContent);
        Assert.True(innerContent.Done);
        Assert.Equal("stop", innerContent.DoneReason);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsExecutionSettingsMustBeSentAsync()
    {
        //Arrange
        var expectedModel = "fake-model";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = ollamaClient.AsChatCompletionService();

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");
        string jsonSettings = """
                                {
                                    "stop": ["stop me"],
                                    "temperature": 0.5,
                                    "top_p": 0.9,
                                    "top_k": 100
                                }
                                """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Act
        await sut.GetStreamingChatMessageContentsAsync(chat, ollamaExecutionSettings).GetAsyncEnumerator().MoveNextAsync();

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Equal(ollamaExecutionSettings.Stop, requestPayload.Options.Stop);
        Assert.Equal(ollamaExecutionSettings.Temperature, requestPayload.Options.Temperature);
        Assert.Equal(ollamaExecutionSettings.TopP, requestPayload.Options.TopP);
        // Assert.Equal(ollamaExecutionSettings.TopK, requestPayload.Options.TopK);
        // Add back once this bugfix is merged
        // https://github.com/awaescher/OllamaSharp/pull/128
    }

    [Fact]
    public async Task GetChatMessageContentsExecutionSettingsMustBeSentAsync()
    {
        //Arrange
        var expectedModel = "fake-model";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
        var sut = ollamaClient.AsChatCompletionService();

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");
        string jsonSettings = """
                                {
                                    "stop": ["stop me"],
                                    "temperature": 0.5,
                                    "top_p": 0.9,
                                    "top_k": 100
                                }
                                """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Act
        await sut.GetChatMessageContentsAsync(chat, ollamaExecutionSettings);

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Equal(ollamaExecutionSettings.Stop, requestPayload.Options.Stop);
        Assert.Equal(ollamaExecutionSettings.Temperature, requestPayload.Options.Temperature);
        Assert.Equal(ollamaExecutionSettings.TopP, requestPayload.Options.TopP);
        // Assert.Equal(ollamaExecutionSettings.TopK, requestPayload.Options.TopK);
        // Add back once this bugfix is merged
        // https://github.com/awaescher/OllamaSharp/pull/128
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
