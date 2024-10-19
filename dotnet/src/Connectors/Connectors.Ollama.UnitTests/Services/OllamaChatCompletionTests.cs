// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
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
    private readonly MultipleHttpMessageHandlerStub _multiMessageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly HttpResponseMessage _defaultResponseMessage;
    public OllamaChatCompletionTests()
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
        //Arrange
        var sut = new OllamaChatCompletionService(
            "fake-model",
            httpClient: this._httpClient);
        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");

        //Act
        await sut.GetChatMessageContentsAsync(chat);

        //Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
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
        var expectedModel = "llama3.2";
        var sut = new OllamaChatCompletionService(
            expectedModel,
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
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Null(requestPayload.Options.Stop);
        Assert.Null(requestPayload.Options.Temperature);
        Assert.Null(requestPayload.Options.TopK);
        Assert.Null(requestPayload.Options.TopP);

        Assert.NotNull(message.ModelId);
        Assert.Equal(expectedModel, message.ModelId);

        // Ollama Sharp always perform streaming even for non-streaming calls,
        // The inner content in this case is the full list of chunks returned by the Ollama Client.
        Assert.NotNull(message.InnerContent);
        Assert.IsType<ChatDoneResponseStream>(message.InnerContent);
        var doneMessage = message.InnerContent as ChatDoneResponseStream;
        Assert.NotNull(doneMessage);
        Assert.True(doneMessage.Done);
        Assert.Equal("stop", doneMessage.DoneReason);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsShouldHaveModelAndInnerContentAsync()
    {
        //Arrange
        var expectedModel = "llama3.2";
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
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
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
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
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
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
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
        using var response = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt")),
        };

        this._multiMessageHandlerStub.ResponsesToReturn = [response];

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
        var requestContent = this._multiMessageHandlerStub.GetRequestContentAsString(0);

        Assert.NotNull(messages);
        var message = messages.SingleOrDefault();
        Assert.NotNull(message);

        // Assert
        var requestBody = this._multiMessageHandlerStub.GetRequestContentAsString(0);
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
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

    [Fact]
    public async Task GetChatMessageContentsShouldAdvertiseAndTriggerToolAsync()
    {
        //Arrange
        var targetModel = "llama3.2";
        using var firstResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_function_call_response.txt")),
        };
        using var secondResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt"))
        };

        this._multiMessageHandlerStub.ResponsesToReturn = [firstResponse, secondResponse];

        var sut = new OllamaChatCompletionService(
            targetModel,
            httpClient: this._httpClient);

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");
        Kernel kernel = new();
        var invocationCount = 0;
        kernel.Plugins.AddFromFunctions("TestPlugin", [KernelFunctionFactory.CreateFromMethod((string testInput) =>
        {
            invocationCount++;
            return "Test output";
        }, "TestFunction")]);

        var settings = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        //Act
        var messages = await sut.GetChatMessageContentsAsync(chat, settings, kernel, CancellationToken.None);

        //Assert
        var requestContent = this._multiMessageHandlerStub.GetRequestContentAsString(0);

        Assert.NotNull(messages);
        var message = messages.SingleOrDefault();
        Assert.NotNull(message);

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
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

        Assert.Equal(1, invocationCount);

        Assert.NotNull(message.ModelId);
        Assert.Equal(targetModel, message.ModelId);
        Assert.NotNull(message.InnerContent);
        Assert.IsType<ChatDoneResponseStream>(message.InnerContent);
        var innerContent = message.InnerContent as ChatDoneResponseStream;
        Assert.NotNull(innerContent);
        Assert.True(innerContent.Done);
        Assert.Equal("stop", innerContent.DoneReason);
    }

    [Fact]
    public async Task ItDoesNotChangeDefaultsForToolsAndChoiceIfNeitherOfFunctionCallingConfigurationsSetAsync()
    {
        // Arrange
        var kernel = new Kernel();

        var targetModel = "llama3.2";
        using var response = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt"))
        };

        this._multiMessageHandlerStub.ResponsesToReturn = [response];

        var sut = new OllamaChatCompletionService(
            targetModel,
            httpClient: this._httpClient);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Fake prompt");

        var executionSettings = new OllamaPromptExecutionSettings(); // FunctionChoiceBehavior is not set.

        // Act
        await sut.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        var actualRequestContent = this._multiMessageHandlerStub.GetRequestContentAsString(0);
        Assert.NotNull(actualRequestContent);

        Assert.DoesNotContain("\"tools\":[", actualRequestContent);
        Assert.DoesNotContain("\"tool_calls\":[", actualRequestContent);
        Assert.DoesNotContain("\"images\":[", actualRequestContent);
    }

    [Fact]
    public async Task FunctionResultsCanBeProvidedToLLMAsManyResultsInOneChatMessageAsync()
    {
        // Arrange
        Kernel kernel = new();
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt"))
        };
        this._multiMessageHandlerStub.ResponsesToReturn = [responseMessage];

        var sut = new OllamaChatCompletionService("any", httpClient: this._httpClient);

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.Tool,
            [
                new FunctionResultContent(new FunctionCallContent("GetCurrentWeather", "MyPlugin", "1", new KernelArguments() { ["location"] = "Boston, MA" }), "rainy"),
                new FunctionResultContent(new FunctionCallContent("GetWeatherForecast", "MyPlugin", "2", new KernelArguments() { ["location"] = "Boston, MA" }), "sunny")
            ])
        };

        var settings = new OllamaPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        var actualRequestContent = this._multiMessageHandlerStub.GetRequestContentAsString(0);
        Assert.NotNull(actualRequestContent);

        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");
        Assert.Equal(2, messages.GetArrayLength());

        var toolMessage1 = messages[0];
        var toolMessage2 = messages[1];

        Assert.Equal("tool", toolMessage1.GetProperty("role").GetString());
        Assert.Equal("tool", toolMessage2.GetProperty("role").GetString());

        var toolMessage1Content = toolMessage1.GetProperty("content").GetString();
        var toolMessage2Content = toolMessage2.GetProperty("content").GetString();

        Assert.Contains("\"result\":\"rainy\"", toolMessage1Content);
        Assert.Contains("\"tool_call_id\":\"1\"", toolMessage1Content);

        Assert.Contains("\"result\":\"sunny\"", toolMessage2Content);
        Assert.Contains("\"tool_call_id\":\"2\"", toolMessage2Content);
    }

    [Fact]
    public async Task FunctionResultsCanBeProvidedToLLMAsOneResultPerChatMessageAsync()
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt"))
        };
        this._multiMessageHandlerStub.ResponsesToReturn.Add(responseMessage);

        var sut = new OllamaChatCompletionService("any", httpClient: this._httpClient);

        ChatHistory chatHistory =
        [
            new ChatMessageContent(AuthorRole.Tool,
            [
                new FunctionResultContent(new FunctionCallContent("GetCurrentWeather", "MyPlugin", "1", new KernelArguments() { ["location"] = "Boston, MA" }), "rainy"),
            ]),
            new ChatMessageContent(AuthorRole.Tool,
            [
                new FunctionResultContent(new FunctionCallContent("GetWeatherForecast", "MyPlugin", "2", new KernelArguments() { ["location"] = "Boston, MA" }), "sunny")
            ])
        ];

        var settings = new OllamaPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, settings, new());

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._multiMessageHandlerStub.RequestContents[0]!);
        Assert.NotNull(actualRequestContent);

        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");
        Assert.Equal(2, messages.GetArrayLength());

        var toolMessage1 = messages[0];
        var toolMessage2 = messages[1];

        Assert.Equal("tool", toolMessage1.GetProperty("role").GetString());
        Assert.Equal("tool", toolMessage2.GetProperty("role").GetString());

        var toolMessage1Content = toolMessage1.GetProperty("content").GetString();
        var toolMessage2Content = toolMessage2.GetProperty("content").GetString();

        Assert.Contains("\"result\":\"rainy\"", toolMessage1Content);
        Assert.Contains("\"tool_call_id\":\"1\"", toolMessage1Content);

        Assert.Contains("\"result\":\"sunny\"", toolMessage2Content);
        Assert.Contains("\"tool_call_id\":\"2\"", toolMessage2Content);
    }

    [Fact]
    public async Task FunctionCallsShouldBePropagatedToCallersViaChatMessageItemsOfTypeFunctionCallContentAsync()
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_multiple_function_calls_test_response.txt"))
        };
        using var assistantResponseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt"))
        };
        this._multiMessageHandlerStub.ResponsesToReturn = [responseMessage, assistantResponseMessage];

        var sut = new OllamaChatCompletionService("any", httpClient: this._httpClient);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Fake prompt");

        var settings = new OllamaPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };

        // Act
        var result = await sut.GetChatMessageContentAsync(chatHistory, settings, new());

        // Assert
        Assert.NotNull(result);
        Assert.Equal(5, result.Items.Count);

        var getCurrentWeatherFunctionCall = result.Items[0] as FunctionCallContent;
        Assert.NotNull(getCurrentWeatherFunctionCall);
        Assert.Equal("GetCurrentWeather", getCurrentWeatherFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", getCurrentWeatherFunctionCall.PluginName);
        Assert.NotNull(getCurrentWeatherFunctionCall.Id);
        Assert.Equal("Boston, MA", getCurrentWeatherFunctionCall.Arguments?["location"]?.ToString());

        var functionWithExceptionFunctionCall = result.Items[1] as FunctionCallContent;
        Assert.NotNull(functionWithExceptionFunctionCall);
        Assert.Equal("FunctionWithException", functionWithExceptionFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", functionWithExceptionFunctionCall.PluginName);
        Assert.NotNull(functionWithExceptionFunctionCall.Id);
        Assert.Equal("value", functionWithExceptionFunctionCall.Arguments?["argument"]?.ToString());

        var nonExistentFunctionCall = result.Items[2] as FunctionCallContent;
        Assert.NotNull(nonExistentFunctionCall);
        Assert.Equal("NonExistentFunction", nonExistentFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", nonExistentFunctionCall.PluginName);
        Assert.NotNull(nonExistentFunctionCall.Id);
        Assert.Equal("value", nonExistentFunctionCall.Arguments?["argument"]?.ToString());

        var nullArgumentsFunctionCall = result.Items[3] as FunctionCallContent;
        Assert.NotNull(nullArgumentsFunctionCall);
        Assert.Equal("InvalidArguments", nullArgumentsFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", nullArgumentsFunctionCall.PluginName);
        Assert.NotNull(nullArgumentsFunctionCall.Id);
        Assert.Null(nullArgumentsFunctionCall.Arguments);

        var intArgumentsFunctionCall = result.Items[4] as FunctionCallContent;
        Assert.NotNull(intArgumentsFunctionCall);
        Assert.Equal("IntArguments", intArgumentsFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", intArgumentsFunctionCall.PluginName);
        Assert.NotNull(intArgumentsFunctionCall.Id);
        Assert.Equal("36", intArgumentsFunctionCall.Arguments?["age"]?.ToString());
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._multiMessageHandlerStub.Dispose();
        this._defaultResponseMessage.Dispose();
    }
}
