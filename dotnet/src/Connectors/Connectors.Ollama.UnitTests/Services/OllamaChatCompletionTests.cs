// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;
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
        var sut = new OllamaChatCompletionService(
            "fake-model",
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
    public async Task GetChatMessageContentsShouldHaveModelAndInnerContentAsync()
    {
        //Arrange
        var sut = new OllamaChatCompletionService(
            "phi3",
            httpClient: this._httpClient);

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
        Assert.IsType<List<ChatResponseStream>>(message.InnerContent);
        var innerContentList = message.InnerContent as List<ChatResponseStream>;
        Assert.NotNull(innerContentList);
        Assert.NotEmpty(innerContentList);
        var lastMessage = innerContentList.Last();
        var doneMessageChunk = lastMessage as ChatDoneResponseStream;
        Assert.NotNull(doneMessageChunk);
        Assert.True(doneMessageChunk.Done);
        Assert.Equal("stop", doneMessageChunk.DoneReason);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsShouldHaveModelAndInnerContentAsync()
    {
        //Arrange
        var expectedModel = "phi3";
        var sut = new OllamaChatCompletionService(
            expectedModel,
            httpClient: this._httpClient);

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

        Assert.NotNull(lastMessage!.ModelId);
        Assert.Equal(expectedModel, lastMessage.ModelId);

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
        var sut = new OllamaChatCompletionService(
            expectedModel,
            httpClient: this._httpClient);

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
        var sut = new OllamaChatCompletionService(
            "fake-model",
            httpClient: this._httpClient);
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
        Assert.Equal(ollamaExecutionSettings.TopK, requestPayload.Options.TopK);
    }

    [Fact]
    public async Task GetChatMessageContentsExecutionSettingsMustBeSentAsync()
    {
        //Arrange
        var sut = new OllamaChatCompletionService(
            "fake-model",
            httpClient: this._httpClient);
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
        Assert.Equal(ollamaExecutionSettings.TopK, requestPayload.Options.TopK);
    }

    // Function Calling start

    [Fact]
    public async Task GetChatMessageContentsShouldAdvertiseToolAsync()
    {
        //Arrange
        var targetModel = "llama3.2";
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt")),
            StatusCode = System.Net.HttpStatusCode.OK,
        };

        var sut = new OllamaChatCompletionService(
            targetModel,
            httpClient: this._httpClient);

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");
        Kernel kernel = new();
        kernel.Plugins.AddFromFunctions("TestPlugin", [KernelFunctionFactory.CreateFromMethod((string testInput) => { return "Test output"; }, "TestFunction")]);
        var settings = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        //Act
        var messages = await sut.GetChatMessageContentsAsync(chat, settings, kernel, CancellationToken.None);

        //Assert
        var requestContent = this._messageHandlerStub.GetRequestContentAsString();

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
        Assert.Equal(targetModel, requestPayload.Model);

        Assert.NotNull(requestPayload.Tools);
        Assert.NotEmpty(requestPayload.Tools);
        Assert.Equal(1, requestPayload.Tools?.Count());
        var firstTool = requestPayload.Tools?.First()!;
        Assert.Equal("TestPlugin-TestFunction", firstTool.Function!.Name);
        Assert.Single(firstTool.Function!.Parameters!.Properties!);
        Assert.Equal("testInput", firstTool.Function!.Parameters!.Properties!.First().Key);
        Assert.Equal("string", firstTool.Function!.Parameters!.Properties!.First().Value.Type);
        Assert.Equal("testInput", firstTool.Function!.Parameters!.Required!.First());

        Assert.NotNull(message.ModelId);
        Assert.Equal(targetModel, message.ModelId);
        Assert.NotNull(message.InnerContent);
        Assert.IsType<ChatDoneResponseStream>(message.InnerContent);
        var innerContent = message.InnerContent as ChatDoneResponseStream;
        Assert.NotNull(innerContent);
        Assert.True(innerContent.Done);
        Assert.Equal("stop", innerContent.DoneReason);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
