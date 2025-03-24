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
using OllamaSharp;
using OllamaSharp.Models.Chat;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests.Services;

public sealed class OllamaChatCompletionTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly MultipleHttpMessageHandlerStub _multiMessageHandlerStub;
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
        using var ollamaClient = new OllamaApiClient(this._httpClient, "fake-model");
        var sut = ollamaClient.AsChatCompletionService();
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
        var expectedModel = "llama3.2";
        using var ollamaClient = new OllamaApiClient(this._httpClient, expectedModel);
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
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
        Assert.NotNull(requestPayload);
        Assert.NotNull(requestPayload.Options);
        Assert.Null(requestPayload.Options.Stop);
        Assert.Null(requestPayload.Options.Temperature);
        Assert.Null(requestPayload.Options.TopK);
        Assert.Null(requestPayload.Options.TopP);

        Assert.NotNull(lastMessage);
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
        var expectedModel = "llama3.2";
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
#pragma warning disable CS0612 // OllamaPromptExecutionSettings is obsolete
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);
#pragma warning restore CS0612

        // Act
        await sut.GetStreamingChatMessageContentsAsync(chat, ollamaExecutionSettings).GetAsyncEnumerator().MoveNextAsync();

        // Assert
        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(this._multiMessageHandlerStub.RequestContents[0]);
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

        using var ollamaClient = new OllamaApiClient(this._httpClient, targetModel);
        var sut = ollamaClient.AsChatCompletionService();

        var chat = new ChatHistory();
        chat.AddMessage(AuthorRole.User, "fake-text");
        Kernel kernel = new();
        kernel.Plugins.AddFromFunctions("TestPlugin", [KernelFunctionFactory.CreateFromMethod((string testInput) => { return "Test output"; }, "TestFunction")]);
        var settings = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        //Act
        var messages = await sut.GetChatMessageContentsAsync(chat, settings, kernel, CancellationToken.None);

        //Assert
        var requestContent = this._multiMessageHandlerStub.GetRequestContentAsString(0);
        Assert.NotNull(requestContent);
        Assert.NotNull(messages);
        var message = messages.SingleOrDefault();
        Assert.NotNull(message);

        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(requestContent);
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

        var firstTool = JsonSerializer.Deserialize<Tool>((requestPayload.Tools?.Cast<JsonElement>().First()!).Value);
        Assert.Equal("TestPlugin_TestFunction", firstTool!.Function!.Name);
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

        var sut = Kernel.CreateBuilder()
            .AddOllamaChatCompletion(targetModel, this._httpClient)
            .Build()
            .GetRequiredService<IChatCompletionService>();

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
        var requestBody = this._multiMessageHandlerStub.GetRequestContentAsString(0);
        Assert.NotNull(requestBody);

        var requestPayload = JsonSerializer.Deserialize<ChatRequest>(requestBody);
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

        var firstTool = JsonSerializer.Deserialize<Tool>((requestPayload.Tools?.Cast<JsonElement>().First()!).Value);
        Assert.Equal("TestPlugin_TestFunction", firstTool!.Function!.Name);
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

        using var ollamaClient = new OllamaApiClient(this._httpClient, targetModel);
        var sut = ollamaClient.AsChatCompletionService();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Fake prompt");

        var executionSettings = new OllamaPromptExecutionSettings(); // FunctionChoiceBehavior is not set.

        // Act
        await sut.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        var actualRequestContent = this._multiMessageHandlerStub.GetRequestContentAsString(0);
        Assert.NotNull(actualRequestContent);

        Assert.DoesNotContain("\"tools\":[", actualRequestContent);
        // Add back when this PR is merged.
        // https://github.com/awaescher/OllamaSharp/pull/129
        // Assert.DoesNotContain("\"tool_calls\":[", actualRequestContent);
        // Assert.DoesNotContain("\"images\":[", actualRequestContent);
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

        var sut = Kernel.CreateBuilder()
            .AddOllamaChatCompletion("any", this._httpClient)
            .Build()
            .GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.Tool,
            [
                new FunctionResultContent(new FunctionCallContent("GetCurrentWeather", "MyPlugin", "1", new KernelArguments() { ["location"] = "Boston, MA" }), "rainy"),
                new FunctionResultContent(new FunctionCallContent("GetWeatherForecast", "MyPlugin", "2", new KernelArguments() { ["location"] = "Boston, MA" }), "sunny")
            ])
        };

        var settings = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

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

        Assert.Contains("\"Result\":\"rainy\"", toolMessage1Content);
        Assert.Contains("\"CallId\":\"1\"", toolMessage1Content);
        Assert.Contains("\"Result\":\"sunny\"", toolMessage2Content);
        Assert.Contains("\"CallId\":\"2\"", toolMessage2Content);
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

        using var ollamaClient = new OllamaApiClient(this._httpClient, "any");
        var sut = ollamaClient.AsChatCompletionService();

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

        var settings = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

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

        Assert.Contains("\"Result\":\"rainy\"", toolMessage1Content);
        Assert.Contains("\"CallId\":\"1\"", toolMessage1Content);
        Assert.Contains("\"Result\":\"sunny\"", toolMessage2Content);
        Assert.Contains("\"CallId\":\"2\"", toolMessage2Content);
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

        using var ollamaClient = new OllamaApiClient(this._httpClient, "any");
        var sut = ollamaClient.AsChatCompletionService();

        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("Fake prompt");

        var settings = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };

        // Act
        var result = await sut.GetChatMessageContentAsync(chatHistory, settings, new());

        // Assert
        Assert.NotNull(result);
        Assert.Equal(5, result.Items.Count);

        var getCurrentWeatherFunctionCall = result.Items[0] as FunctionCallContent;
        Assert.NotNull(getCurrentWeatherFunctionCall);
        Assert.Equal("MyPlugin_GetCurrentWeather", getCurrentWeatherFunctionCall.FunctionName);
        Assert.NotNull(getCurrentWeatherFunctionCall.Id);
        Assert.Equal("Boston, MA", getCurrentWeatherFunctionCall.Arguments?["location"]?.ToString());

        var functionWithExceptionFunctionCall = result.Items[1] as FunctionCallContent;
        Assert.NotNull(functionWithExceptionFunctionCall);
        Assert.Equal("MyPlugin_FunctionWithException", functionWithExceptionFunctionCall.FunctionName);
        Assert.NotNull(functionWithExceptionFunctionCall.Id);
        Assert.Equal("value", functionWithExceptionFunctionCall.Arguments?["argument"]?.ToString());

        var nonExistentFunctionCall = result.Items[2] as FunctionCallContent;
        Assert.NotNull(nonExistentFunctionCall);
        Assert.Equal("MyPlugin_NonExistentFunction", nonExistentFunctionCall.FunctionName);
        Assert.NotNull(nonExistentFunctionCall.Id);
        Assert.Equal("value", nonExistentFunctionCall.Arguments?["argument"]?.ToString());

        var nullArgumentsFunctionCall = result.Items[3] as FunctionCallContent;
        Assert.NotNull(nullArgumentsFunctionCall);
        Assert.Equal("MyPlugin_InvalidArguments", nullArgumentsFunctionCall.FunctionName);
        Assert.NotNull(nullArgumentsFunctionCall.Id);
        Assert.Null(nullArgumentsFunctionCall.Arguments);

        var intArgumentsFunctionCall = result.Items[4] as FunctionCallContent;
        Assert.NotNull(intArgumentsFunctionCall);
        Assert.Equal("MyPlugin_IntArguments", intArgumentsFunctionCall.FunctionName);
        Assert.NotNull(intArgumentsFunctionCall.Id);
        Assert.Equal("36", intArgumentsFunctionCall.Arguments?["age"]?.ToString());
    }

    [Fact]
    public async Task GetChatMessageContentsWithFunctionCallAsync()
    {
        // Arrange
        int functionCallCount = 0;

        var kernel = Kernel.CreateBuilder().Build();
        var function1 = KernelFunctionFactory.CreateFromMethod((string location) =>
        {
            functionCallCount++;
            return "Some weather";
        }, "GetCurrentWeather");

        var function2 = KernelFunctionFactory.CreateFromMethod((string argument) =>
        {
            functionCallCount++;
            throw new ArgumentException("Some exception");
        }, "FunctionWithException");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]));

        var sut = Kernel.CreateBuilder()
            .AddOllamaChatCompletion("llama3.2", this._httpClient)
            .Build()
            .GetRequiredService<IChatCompletionService>();

        var settings = new OllamaPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/chat_completion_multiple_function_calls_test_response.txt")) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.txt")) };

        this._multiMessageHandlerStub.ResponsesToReturn = [response1, response2];

        // Act
        var result = await sut.GetChatMessageContentsAsync(new ChatHistory("System message"), settings, kernel);

        // Assert
        Assert.True(result.Count > 0);
        Assert.Equal("This is test completion response", result[0].Content);

        Assert.Equal(2, functionCallCount);
    }

    [Fact]
    public async Task GetChatMessageContentsWithFunctionCallMaximumAutoInvokeAttemptsAsync()
    {
        // Arrange
        const int DefaultMaximumAutoInvokeAttempts = 128;
        const int ModelResponsesCount = 129;

        int functionCallCount = 0;

        var kernel = Kernel.CreateBuilder().Build();
        var function = KernelFunctionFactory.CreateFromMethod((string testInput) =>
        {
            functionCallCount++;
            return "Some output";
        }, "TestFunction");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("TestPlugin", [function]));

        var sut = Kernel.CreateBuilder()
            .AddOllamaChatCompletion("llama3.2", this._httpClient)
            .Build()
            .GetRequiredService<IChatCompletionService>();

        var settings = new OllamaPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        var responses = new List<HttpResponseMessage>();

        try
        {
            for (var i = 0; i < ModelResponsesCount; i++)
            {
                responses.Add(new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/chat_completion_function_call_response.txt")) });
            }

            this._multiMessageHandlerStub.ResponsesToReturn = responses;

            // Act
            var result = await sut.GetChatMessageContentsAsync(new ChatHistory("System message"), settings, kernel);

            // Assert
            Assert.Equal(DefaultMaximumAutoInvokeAttempts, functionCallCount);
        }
        finally
        {
            responses.ForEach(r => r.Dispose());
        }
    }

    [Fact(Skip = "AutoFunctionInvocationFilter is not supported yet")]
    public async Task GetChatMessageContentShouldSendMutatedChatHistoryToLLMAsync()
    {
        // Arrange
        static void MutateChatHistory(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Remove the function call messages from the chat history to reduce token count.
            context.ChatHistory.RemoveRange(1, 2); // Remove the `Date` function call and function result messages.

            next(context);
        }

        var kernel = new Kernel();
        kernel.ImportPluginFromFunctions("TestPlugin", [KernelFunctionFactory.CreateFromMethod(() => "rainy", "TestFunction")]);
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(MutateChatHistory));
        this._multiMessageHandlerStub.ResponsesToReturn.Clear();
        this._defaultResponseMessage.Dispose();

        using var firstResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_function_call_response.txt")) };
        using var secondResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_test_response.txt")) };
        this._multiMessageHandlerStub.ResponsesToReturn = [firstResponse, secondResponse];

        using var ollamaClient = new OllamaApiClient(this._httpClient, "any");
        var sut = ollamaClient.AsChatCompletionService();

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What time is it?"),
            new ChatMessageContent(AuthorRole.Assistant, [
                new FunctionCallContent("Date", "TestPlugin", "2")
            ]),
            new ChatMessageContent(AuthorRole.Tool, [
                new FunctionResultContent("Date",  "TestPlugin", "2", "rainy")
            ]),
            new ChatMessageContent(AuthorRole.Assistant, "08/06/2024 00:00:00"),
            new ChatMessageContent(AuthorRole.User, "Given the current time of day and weather, what is the likely color of the sky in Boston?")
        };

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, new OllamaPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }, kernel);

        // Assert
        var actualRequestContent = this._multiMessageHandlerStub.GetRequestContentAsString(0);
        Assert.NotNull(actualRequestContent);

        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");
        Assert.Equal(5, messages.GetArrayLength());

        var userFirstPrompt = messages[0];
        Assert.Equal("user", userFirstPrompt.GetProperty("role").GetString());
        Assert.Equal("What time is it?", userFirstPrompt.GetProperty("content").ToString());

        var assistantFirstResponse = messages[1];
        Assert.Equal("assistant", assistantFirstResponse.GetProperty("role").GetString());
        Assert.Equal("08/06/2024 00:00:00", assistantFirstResponse.GetProperty("content").GetString());

        var userSecondPrompt = messages[2];
        Assert.Equal("user", userSecondPrompt.GetProperty("role").GetString());
        Assert.Equal("Given the current time of day and weather, what is the likely color of the sky in Boston?", userSecondPrompt.GetProperty("content").ToString());

        var assistantSecondResponse = messages[3];
        Assert.Equal("assistant", assistantSecondResponse.GetProperty("role").GetString());
        Assert.Equal("TestPlugin-TestFunction", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("function").GetProperty("name").GetString());

        var functionResult = messages[4];
        Assert.Equal("tool", functionResult.GetProperty("role").GetString());
        Assert.Contains("\"result\":\"rainy\"", functionResult.GetProperty("content").GetString());
    }

    private sealed class AutoFunctionInvocationFilter : IAutoFunctionInvocationFilter
    {
        private readonly Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task> _callback;

        public AutoFunctionInvocationFilter(Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task> callback)
        {
            Verify.NotNull(callback, nameof(callback));
            this._callback = callback;
        }

        public AutoFunctionInvocationFilter(Action<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>> callback)
        {
            Verify.NotNull(callback, nameof(callback));
            this._callback = (c, n) => { callback(c, n); return Task.CompletedTask; };
        }

        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            await this._callback(context, next);
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._multiMessageHandlerStub.Dispose();
        this._defaultResponseMessage.Dispose();
    }
}
