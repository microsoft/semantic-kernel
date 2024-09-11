﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using OpenAI;
using OpenAI.Chat;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="OpenAIChatCompletionService"/>
/// </summary>
public sealed class OpenAIChatCompletionServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly MultipleHttpMessageHandlerStub _multiMessageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly OpenAIFunction _timepluginDate, _timepluginNow;
    private readonly OpenAIPromptExecutionSettings _executionSettings;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;
    private readonly ChatHistory _chatHistoryForTest = [new ChatMessageContent(AuthorRole.User, "test")];

    public OpenAIChatCompletionServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._multiMessageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();

        IList<KernelFunctionMetadata> functions = KernelPluginFactory.CreateFromFunctions("TimePlugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod((string? format = null) => DateTime.Now.Date.ToString(format, CultureInfo.InvariantCulture), "Date", "TimePlugin.Date"),
            KernelFunctionFactory.CreateFromMethod((string? format = null) => DateTime.Now.ToString(format, CultureInfo.InvariantCulture), "Now", "TimePlugin.Now"),
        }).GetFunctionsMetadata();

        this._timepluginDate = functions[0].ToOpenAIFunction();
        this._timepluginNow = functions[1].ToOpenAIFunction();

        this._executionSettings = new()
        {
            ToolCallBehavior = ToolCallBehavior.EnableFunctions([this._timepluginDate, this._timepluginNow])
        };
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithApiKeyWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new OpenAIChatCompletionService("model-id", "api-key", "organization", loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIChatCompletionService("model-id", "api-key", "organization");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [InlineData("http://localhost:1234/v1/chat/completions", "http://localhost:1234/v1/chat/completions")] // Uses full path when provided
    [InlineData("http://localhost:1234/", "http://localhost:1234/v1/chat/completions")]
    [InlineData("http://localhost:8080", "http://localhost:8080/v1/chat/completions")]
    [InlineData("https://something:8080", "https://something:8080/v1/chat/completions")] // Accepts TLS Secured endpoints
    public async Task ItUsesCustomEndpointsWhenProvidedDirectlyAsync(string endpointProvided, string expectedEndpoint)
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "any", apiKey: null, httpClient: this._httpClient, endpoint: new Uri(endpointProvided));
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };

        // Act
        await chatCompletion.GetChatMessageContentsAsync(this._chatHistoryForTest, this._executionSettings);

        // Assert
        Assert.Equal(expectedEndpoint, this._messageHandlerStub.RequestUri!.ToString());
    }

    [Theory]
    [InlineData("http://localhost:1234/v1/chat/completions", "http://localhost:1234/v1/chat/completions")] // Uses full path when provided
    [InlineData("http://localhost:1234/", "http://localhost:1234/v1/chat/completions")]
    [InlineData("http://localhost:8080", "http://localhost:8080/v1/chat/completions")]
    [InlineData("https://something:8080", "https://something:8080/v1/chat/completions")] // Accepts TLS Secured endpoints
    public async Task ItUsesCustomEndpointsWhenProvidedAsBaseAddressAsync(string endpointProvided, string expectedEndpoint)
    {
        // Arrange
        this._httpClient.BaseAddress = new Uri(endpointProvided);
        var chatCompletion = new OpenAIChatCompletionService(modelId: "any", apiKey: null, httpClient: this._httpClient, endpoint: new Uri(endpointProvided));
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };

        // Act
        await chatCompletion.GetChatMessageContentsAsync(this._chatHistoryForTest, this._executionSettings);

        // Assert
        Assert.Equal(expectedEndpoint, this._messageHandlerStub.RequestUri!.ToString());
    }

    [Fact]
    public async Task ItUsesHttpClientEndpointIfProvidedEndpointIsMissingAsync()
    {
        // Arrange
        this._httpClient.BaseAddress = new Uri("http://localhost:12312");
        var chatCompletion = new OpenAIChatCompletionService(modelId: "any", apiKey: null, httpClient: this._httpClient, endpoint: null!);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };

        // Act
        await chatCompletion.GetChatMessageContentsAsync(this._chatHistoryForTest, this._executionSettings);

        // Assert
        Assert.Equal("http://localhost:12312/v1/chat/completions", this._messageHandlerStub.RequestUri!.ToString());
    }

    [Fact]
    public async Task ItUsesDefaultEndpointIfProvidedEndpointIsMissingAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "any", apiKey: "abc", httpClient: this._httpClient, endpoint: null!);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };

        // Act
        await chatCompletion.GetChatMessageContentsAsync(this._chatHistoryForTest, this._executionSettings);

        // Assert
        Assert.Equal("https://api.openai.com/v1/chat/completions", this._messageHandlerStub.RequestUri!.ToString());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithOpenAIClientWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var client = new OpenAIClient("key");
        var service = includeLoggerFactory ?
            new OpenAIChatCompletionService("model-id", client, loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIChatCompletionService("model-id", client);

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Fact]
    public async Task ItCreatesCorrectFunctionToolCallsWhenUsingAutoAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };

        // Act
        await chatCompletion.GetChatMessageContentsAsync([new ChatMessageContent(AuthorRole.User, "test")], this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(2, optionsJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("TimePlugin-Date", optionsJson.GetProperty("tools")[0].GetProperty("function").GetProperty("name").GetString());
        Assert.Equal("TimePlugin-Now", optionsJson.GetProperty("tools")[1].GetProperty("function").GetProperty("name").GetString());
    }

    [Fact]
    public async Task ItCreatesCorrectFunctionToolCallsWhenUsingNowAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        this._executionSettings.ToolCallBehavior = ToolCallBehavior.RequireFunction(this._timepluginNow);

        // Act
        await chatCompletion.GetChatMessageContentsAsync(this._chatHistoryForTest, this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(1, optionsJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("TimePlugin-Now", optionsJson.GetProperty("tools")[0].GetProperty("function").GetProperty("name").GetString());
    }

    [Fact]
    public async Task ItCreatesNoFunctionsWhenUsingNoneAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        this._executionSettings.ToolCallBehavior = null;

        // Act
        await chatCompletion.GetChatMessageContentsAsync(this._chatHistoryForTest, this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.False(optionsJson.TryGetProperty("functions", out var _));
    }

    [Fact]
    public async Task ItAddsIdToChatMessageAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.Tool, "Hello", metadata: new Dictionary<string, object?>() { { OpenAIChatMessageContent.ToolIdProperty, "John Doe" } });

        // Act
        await chatCompletion.GetChatMessageContentsAsync(chatHistory, this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);
        Assert.Equal(1, optionsJson.GetProperty("messages").GetArrayLength());
        Assert.Equal("John Doe", optionsJson.GetProperty("messages")[0].GetProperty("tool_call_id").GetString());
    }

    [Fact]
    public async Task ItGetChatMessageContentsShouldHaveModelIdDefinedAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse, Encoding.UTF8, "application/json") };

        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");

        // Act
        var chatMessage = await chatCompletion.GetChatMessageContentAsync(chatHistory, this._executionSettings);

        // Assert
        Assert.NotNull(chatMessage.ModelId);
        Assert.Equal("gpt-3.5-turbo", chatMessage.ModelId);
    }

    [Fact]
    public async Task ItGetTextContentsShouldHaveModelIdDefinedAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse, Encoding.UTF8, "application/json") };

        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");

        // Act
        var textContent = await chatCompletion.GetTextContentAsync("hello", this._executionSettings);

        // Assert
        Assert.NotNull(textContent.ModelId);
        Assert.Equal("gpt-3.5-turbo", textContent.ModelId);
    }

    [Fact]
    public async Task GetStreamingTextContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new OpenAIChatCompletionService("model-id", "api-key", "organization", this._httpClient);
        using var stream = File.OpenRead("TestData/chat_completion_streaming_test_response.txt");

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act & Assert
        var enumerator = service.GetStreamingTextContentsAsync("Prompt").GetAsyncEnumerator();

        await enumerator.MoveNextAsync();
        Assert.Equal("Test chat streaming response", enumerator.Current.Text);

        await enumerator.MoveNextAsync();
        Assert.Equal("Stop", enumerator.Current.Metadata?["FinishReason"]);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new OpenAIChatCompletionService("model-id", "api-key", "organization", this._httpClient);
        using var stream = File.OpenRead("TestData/chat_completion_streaming_test_response.txt");

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act & Assert
        var enumerator = service.GetStreamingChatMessageContentsAsync([]).GetAsyncEnumerator();

        await enumerator.MoveNextAsync();
        Assert.Equal("Test chat streaming response", enumerator.Current.Content);

        await enumerator.MoveNextAsync();
        Assert.Equal("Stop", enumerator.Current.Metadata?["FinishReason"]);
    }

    [Fact]
    public async Task ItAddsSystemMessageAsync()
    {
        // Arrange
        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent(ChatCompletionResponse) };
        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");

        // Act
        await chatCompletion.GetChatMessageContentsAsync(chatHistory, this._executionSettings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");
        Assert.Equal(1, messages.GetArrayLength());

        Assert.Equal("Hello", messages[0].GetProperty("content").GetString());
        Assert.Equal("user", messages[0].GetProperty("role").GetString());
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWithFunctionCallAsync()
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

        using var multiHttpClient = new HttpClient(this._multiMessageHandlerStub, false);
        var service = new OpenAIChatCompletionService("model-id", "api-key", "organization-id", multiHttpClient, this._mockLoggerFactory.Object);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_multiple_function_calls_test_response.txt")) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_test_response.txt")) };

        this._multiMessageHandlerStub.ResponsesToReturn = [response1, response2];

        // Act & Assert
        var enumerator = service.GetStreamingChatMessageContentsAsync([], settings, kernel).GetAsyncEnumerator();

        await enumerator.MoveNextAsync();
        Assert.Equal("Test chat streaming response", enumerator.Current.Content);
        Assert.Equal("ToolCalls", enumerator.Current.Metadata?["FinishReason"]);

        await enumerator.MoveNextAsync();
        Assert.Equal("ToolCalls", enumerator.Current.Metadata?["FinishReason"]);

        // Keep looping until the end of stream
        while (await enumerator.MoveNextAsync())
        {
        }

        Assert.Equal(2, functionCallCount);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWithFunctionCallMaximumAutoInvokeAttemptsAsync()
    {
        // Arrange
        const int DefaultMaximumAutoInvokeAttempts = 128;
        const int ModelResponsesCount = 129;

        int functionCallCount = 0;

        var kernel = Kernel.CreateBuilder().Build();
        var function = KernelFunctionFactory.CreateFromMethod((string location) =>
        {
            functionCallCount++;
            return "Some weather";
        }, "GetCurrentWeather");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]));
        using var multiHttpClient = new HttpClient(this._multiMessageHandlerStub, false);
        var service = new OpenAIChatCompletionService("model-id", "api-key", httpClient: multiHttpClient, loggerFactory: this._mockLoggerFactory.Object);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        var responses = new List<HttpResponseMessage>();

        for (var i = 0; i < ModelResponsesCount; i++)
        {
            responses.Add(new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_single_function_call_test_response.txt")) });
        }

        this._multiMessageHandlerStub.ResponsesToReturn = responses;

        // Act & Assert
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync([], settings, kernel))
        {
            Assert.Equal("Test chat streaming response", chunk.Content);
        }

        Assert.Equal(DefaultMaximumAutoInvokeAttempts, functionCallCount);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWithRequiredFunctionCallAsync()
    {
        // Arrange
        int functionCallCount = 0;

        var kernel = Kernel.CreateBuilder().Build();
        var function = KernelFunctionFactory.CreateFromMethod((string location) =>
        {
            functionCallCount++;
            return "Some weather";
        }, "GetCurrentWeather");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);
        var openAIFunction = plugin.GetFunctionsMetadata().First().ToOpenAIFunction();

        kernel.Plugins.Add(plugin);
        using var multiHttpClient = new HttpClient(this._multiMessageHandlerStub, false);
        var service = new OpenAIChatCompletionService("model-id", "api-key", httpClient: multiHttpClient, loggerFactory: this._mockLoggerFactory.Object);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.RequireFunction(openAIFunction, autoInvoke: true) };

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_single_function_call_test_response.txt")) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_test_response.txt")) };

        this._multiMessageHandlerStub.ResponsesToReturn = [response1, response2];

        // Act & Assert
        var enumerator = service.GetStreamingChatMessageContentsAsync([], settings, kernel).GetAsyncEnumerator();

        // Function Tool Call Streaming (One Chunk)
        await enumerator.MoveNextAsync();
        Assert.Equal("Test chat streaming response", enumerator.Current.Content);
        Assert.Equal("ToolCalls", enumerator.Current.Metadata?["FinishReason"]);

        // Chat Completion Streaming (1st Chunk)
        await enumerator.MoveNextAsync();
        Assert.Null(enumerator.Current.Metadata?["FinishReason"]);

        // Chat Completion Streaming (2nd Chunk)
        await enumerator.MoveNextAsync();
        Assert.Equal("Stop", enumerator.Current.Metadata?["FinishReason"]);

        Assert.Equal(1, functionCallCount);

        var requestContents = this._multiMessageHandlerStub.RequestContents;

        Assert.Equal(2, requestContents.Count);

        requestContents.ForEach(Assert.NotNull);

        var firstContent = Encoding.UTF8.GetString(requestContents[0]!);
        var secondContent = Encoding.UTF8.GetString(requestContents[1]!);

        var firstContentJson = JsonSerializer.Deserialize<JsonElement>(firstContent);
        var secondContentJson = JsonSerializer.Deserialize<JsonElement>(secondContent);

        Assert.Equal(1, firstContentJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("MyPlugin-GetCurrentWeather", firstContentJson.GetProperty("tool_choice").GetProperty("function").GetProperty("name").GetString());

        Assert.Equal("none", secondContentJson.GetProperty("tool_choice").GetString());
    }

    [Fact]
    public async Task GetChatMessageContentsUsesPromptAndSettingsCorrectlyAsync()
    {
        // Arrange
        const string Prompt = "This is test prompt";
        const string SystemMessage = "This is test system message";

        var service = new OpenAIChatCompletionService("model-id", "api-key", httpClient: this._httpClient);
        var settings = new OpenAIPromptExecutionSettings() { ChatSystemPrompt = SystemMessage };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.json"))
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => service);
        Kernel kernel = builder.Build();

        // Act
        var result = await kernel.InvokePromptAsync(Prompt, new(settings));

        // Assert
        Assert.Equal("Test chat response", result.ToString());

        var requestContentByteArray = this._messageHandlerStub.RequestContent;

        Assert.NotNull(requestContentByteArray);

        var requestContent = JsonSerializer.Deserialize<JsonElement>(Encoding.UTF8.GetString(requestContentByteArray));

        var messages = requestContent.GetProperty("messages");

        Assert.Equal(2, messages.GetArrayLength());

        Assert.Equal(SystemMessage, messages[0].GetProperty("content").GetString());
        Assert.Equal("system", messages[0].GetProperty("role").GetString());

        Assert.Equal(Prompt, messages[1].GetProperty("content").GetString());
        Assert.Equal("user", messages[1].GetProperty("role").GetString());
    }

    [Fact]
    public async Task GetChatMessageContentsWithChatMessageContentItemCollectionAndSettingsCorrectlyAsync()
    {
        // Arrange
        const string Prompt = "This is test prompt";
        const string SystemMessage = "This is test system message";
        const string AssistantMessage = "This is assistant message";
        const string CollectionItemPrompt = "This is collection item prompt";

        var chatCompletion = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);
        var settings = new OpenAIPromptExecutionSettings() { ChatSystemPrompt = SystemMessage };

        using var response = new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(ChatCompletionResponse) };
        this._messageHandlerStub.ResponseToReturn = response;

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(Prompt);
        chatHistory.AddAssistantMessage(AssistantMessage);
        chatHistory.AddUserMessage(
        [
            new TextContent(CollectionItemPrompt),
            new ImageContent(new Uri("https://image"))
        ]);

        // Act
        await chatCompletion.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");

        Assert.Equal(4, messages.GetArrayLength());

        Assert.Equal(SystemMessage, messages[0].GetProperty("content").GetString());
        Assert.Equal("system", messages[0].GetProperty("role").GetString());

        Assert.Equal(Prompt, messages[1].GetProperty("content").GetString());
        Assert.Equal("user", messages[1].GetProperty("role").GetString());

        Assert.Equal(AssistantMessage, messages[2].GetProperty("content").GetString());
        Assert.Equal("assistant", messages[2].GetProperty("role").GetString());

        var contentItems = messages[3].GetProperty("content");
        Assert.Equal(2, contentItems.GetArrayLength());
        Assert.Equal(CollectionItemPrompt, contentItems[0].GetProperty("text").GetString());
        Assert.Equal("text", contentItems[0].GetProperty("type").GetString());
        Assert.Equal("https://image/", contentItems[1].GetProperty("image_url").GetProperty("url").GetString());
        Assert.Equal("image_url", contentItems[1].GetProperty("type").GetString());
    }

    [Fact]
    public async Task FunctionCallsShouldBePropagatedToCallersViaChatMessageItemsOfTypeFunctionCallContentAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_multiple_function_calls_test_response.json"))
        };

        var sut = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Fake prompt");

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        // Act
        var result = await sut.GetChatMessageContentAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(5, result.Items.Count);

        var getCurrentWeatherFunctionCall = result.Items[0] as FunctionCallContent;
        Assert.NotNull(getCurrentWeatherFunctionCall);
        Assert.Equal("GetCurrentWeather", getCurrentWeatherFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", getCurrentWeatherFunctionCall.PluginName);
        Assert.Equal("1", getCurrentWeatherFunctionCall.Id);
        Assert.Equal("Boston, MA", getCurrentWeatherFunctionCall.Arguments?["location"]?.ToString());

        var functionWithExceptionFunctionCall = result.Items[1] as FunctionCallContent;
        Assert.NotNull(functionWithExceptionFunctionCall);
        Assert.Equal("FunctionWithException", functionWithExceptionFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", functionWithExceptionFunctionCall.PluginName);
        Assert.Equal("2", functionWithExceptionFunctionCall.Id);
        Assert.Equal("value", functionWithExceptionFunctionCall.Arguments?["argument"]?.ToString());

        var nonExistentFunctionCall = result.Items[2] as FunctionCallContent;
        Assert.NotNull(nonExistentFunctionCall);
        Assert.Equal("NonExistentFunction", nonExistentFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", nonExistentFunctionCall.PluginName);
        Assert.Equal("3", nonExistentFunctionCall.Id);
        Assert.Equal("value", nonExistentFunctionCall.Arguments?["argument"]?.ToString());

        var invalidArgumentsFunctionCall = result.Items[3] as FunctionCallContent;
        Assert.NotNull(invalidArgumentsFunctionCall);
        Assert.Equal("InvalidArguments", invalidArgumentsFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", invalidArgumentsFunctionCall.PluginName);
        Assert.Equal("4", invalidArgumentsFunctionCall.Id);
        Assert.Null(invalidArgumentsFunctionCall.Arguments);
        Assert.NotNull(invalidArgumentsFunctionCall.Exception);
        Assert.Equal("Error: Function call arguments were invalid JSON.", invalidArgumentsFunctionCall.Exception.Message);
        Assert.NotNull(invalidArgumentsFunctionCall.Exception.InnerException);

        var intArgumentsFunctionCall = result.Items[4] as FunctionCallContent;
        Assert.NotNull(intArgumentsFunctionCall);
        Assert.Equal("IntArguments", intArgumentsFunctionCall.FunctionName);
        Assert.Equal("MyPlugin", intArgumentsFunctionCall.PluginName);
        Assert.Equal("5", intArgumentsFunctionCall.Id);
        Assert.Equal("36", intArgumentsFunctionCall.Arguments?["age"]?.ToString());
    }

    [Fact]
    public async Task FunctionCallsShouldBeReturnedToLLMAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(ChatCompletionResponse)
        };

        var sut = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);

        var items = new ChatMessageContentItemCollection
        {
            new FunctionCallContent("GetCurrentWeather", "MyPlugin", "1", new KernelArguments() { ["location"] = "Boston, MA" }),
            new FunctionCallContent("GetWeatherForecast", "MyPlugin", "2", new KernelArguments() { ["location"] = "Boston, MA" })
        };

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.Assistant, items)
        };

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, settings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);

        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");
        Assert.Equal(1, messages.GetArrayLength());

        var assistantMessage = messages[0];
        Assert.Equal("assistant", assistantMessage.GetProperty("role").GetString());

        Assert.Equal(2, assistantMessage.GetProperty("tool_calls").GetArrayLength());

        var tool1 = assistantMessage.GetProperty("tool_calls")[0];
        Assert.Equal("1", tool1.GetProperty("id").GetString());
        Assert.Equal("function", tool1.GetProperty("type").GetString());

        var function1 = tool1.GetProperty("function");
        Assert.Equal("MyPlugin-GetCurrentWeather", function1.GetProperty("name").GetString());
        Assert.Equal("{\"location\":\"Boston, MA\"}", function1.GetProperty("arguments").GetString());

        var tool2 = assistantMessage.GetProperty("tool_calls")[1];
        Assert.Equal("2", tool2.GetProperty("id").GetString());
        Assert.Equal("function", tool2.GetProperty("type").GetString());

        var function2 = tool2.GetProperty("function");
        Assert.Equal("MyPlugin-GetWeatherForecast", function2.GetProperty("name").GetString());
        Assert.Equal("{\"location\":\"Boston, MA\"}", function2.GetProperty("arguments").GetString());
    }

    [Fact]
    public async Task FunctionResultsCanBeProvidedToLLMAsOneResultPerChatMessageAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(ChatCompletionResponse)
        };

        var sut = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.Tool,
            [
                new FunctionResultContent(new FunctionCallContent("GetCurrentWeather", "MyPlugin", "1", new KernelArguments() { ["location"] = "Boston, MA" }), "rainy"),
            ]),
            new ChatMessageContent(AuthorRole.Tool,
            [
                new FunctionResultContent(new FunctionCallContent("GetWeatherForecast", "MyPlugin", "2", new KernelArguments() { ["location"] = "Boston, MA" }), "sunny")
            ])
        };

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, settings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);

        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");
        Assert.Equal(2, messages.GetArrayLength());

        var assistantMessage = messages[0];
        Assert.Equal("tool", assistantMessage.GetProperty("role").GetString());
        Assert.Equal("rainy", assistantMessage.GetProperty("content").GetString());
        Assert.Equal("1", assistantMessage.GetProperty("tool_call_id").GetString());

        var assistantMessage2 = messages[1];
        Assert.Equal("tool", assistantMessage2.GetProperty("role").GetString());
        Assert.Equal("sunny", assistantMessage2.GetProperty("content").GetString());
        Assert.Equal("2", assistantMessage2.GetProperty("tool_call_id").GetString());
    }

    [Fact]
    public async Task FunctionResultsCanBeProvidedToLLMAsManyResultsInOneChatMessageAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(ChatCompletionResponse)
        };

        var sut = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.Tool,
            [
                new FunctionResultContent(new FunctionCallContent("GetCurrentWeather", "MyPlugin", "1", new KernelArguments() { ["location"] = "Boston, MA" }), "rainy"),
                new FunctionResultContent(new FunctionCallContent("GetWeatherForecast", "MyPlugin", "2", new KernelArguments() { ["location"] = "Boston, MA" }), "sunny")
            ])
        };

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, settings);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);

        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");
        Assert.Equal(2, messages.GetArrayLength());

        var assistantMessage = messages[0];
        Assert.Equal("tool", assistantMessage.GetProperty("role").GetString());
        Assert.Equal("rainy", assistantMessage.GetProperty("content").GetString());
        Assert.Equal("1", assistantMessage.GetProperty("tool_call_id").GetString());

        var assistantMessage2 = messages[1];
        Assert.Equal("tool", assistantMessage2.GetProperty("role").GetString());
        Assert.Equal("sunny", assistantMessage2.GetProperty("content").GetString());
        Assert.Equal("2", assistantMessage2.GetProperty("tool_call_id").GetString());
    }

    [Theory]
    [InlineData("string", "json_object")]
    [InlineData("string", "text")]
    [InlineData("string", "random")]
    [InlineData("JsonElement.String", "\"json_object\"")]
    [InlineData("JsonElement.String", "\"text\"")]
    [InlineData("JsonElement.String", "\"random\"")]
    [InlineData("ChatResponseFormat", "json_object")]
    [InlineData("ChatResponseFormat", "text")]
    public async Task GetChatMessageInResponseFormatsAsync(string formatType, string formatValue)
    {
        // Assert
        object? format = null;
        switch (formatType)
        {
            case "string":
                format = formatValue;
                break;
            case "JsonElement.String":
                format = JsonSerializer.Deserialize<JsonElement>(formatValue);
                break;
            case "ChatResponseFormat":
                format = formatValue == "text" ? ChatResponseFormat.Text : ChatResponseFormat.JsonObject;
                break;
        }

        var modelId = "gpt-4o";
        var sut = new OpenAIChatCompletionService(modelId, "apiKey", httpClient: this._httpClient);
        OpenAIPromptExecutionSettings executionSettings = new() { ResponseFormat = format };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.json"))
        };

        // Act
        var result = await sut.GetChatMessageContentAsync(this._chatHistoryForTest, executionSettings);

        // Assert
        Assert.NotNull(result);
    }

    [Fact(Skip = "Not working running in the console")]
    public async Task GetInvalidResponseThrowsExceptionAndIsCapturedByDiagnosticsAsync()
    {
        // Arrange
        bool startedChatCompletionsActivity = false;

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = new StringContent("Invalid JSON") };

        var sut = new OpenAIChatCompletionService("model-id", "api-key", httpClient: this._httpClient);

        // Enable ModelDiagnostics
        using var listener = new ActivityListener()
        {
            ShouldListenTo = (activitySource) => true, //activitySource.Name == typeof(ModelDiagnostics).Namespace!,
            ActivityStarted = (activity) =>
            {
                if (activity.OperationName == "chat.completions model-id")
                {
                    startedChatCompletionsActivity = true;
                }
            },
            Sample = (ref ActivityCreationOptions<ActivityContext> options) => ActivitySamplingResult.AllData,
        };

        ActivitySource.AddActivityListener(listener);

        Environment.SetEnvironmentVariable("SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS", "true");
        Environment.SetEnvironmentVariable("SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE", "true");

        // Act & Assert
        await Assert.ThrowsAnyAsync<Exception>(async () => { await sut.GetChatMessageContentsAsync(this._chatHistoryForTest); });

        Assert.True(ModelDiagnostics.HasListeners());
        Assert.True(ModelDiagnostics.IsSensitiveEventsEnabled());
        Assert.True(ModelDiagnostics.IsModelDiagnosticsEnabled());
        Assert.True(startedChatCompletionsActivity);
    }

    [Fact]
    public async Task GetChatMessageContentShouldSendMutatedChatHistoryToLLM()
    {
        // Arrange
        static void MutateChatHistory(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Remove the function call messages from the chat history to reduce token count.
            context.ChatHistory.RemoveRange(1, 2); // Remove the `Date` function call and function result messages.

            next(context);
        }

        var kernel = new Kernel();
        kernel.ImportPluginFromFunctions("MyPlugin", [KernelFunctionFactory.CreateFromMethod(() => "rainy", "GetCurrentWeather")]);
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(MutateChatHistory));

        using var firstResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_single_function_call_test_response.json")) };
        this._messageHandlerStub.ResponseQueue.Enqueue(firstResponse);

        using var secondResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_test_response.json")) };
        this._messageHandlerStub.ResponseQueue.Enqueue(secondResponse);

        var sut = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What time is it?"),
            new ChatMessageContent(AuthorRole.Assistant, [
                new FunctionCallContent("Date", "TimePlugin", "2")
            ]),
            new ChatMessageContent(AuthorRole.Tool, [
                new FunctionResultContent("Date",  "TimePlugin", "2", "rainy")
            ]),
            new ChatMessageContent(AuthorRole.Assistant, "08/06/2024 00:00:00"),
            new ChatMessageContent(AuthorRole.User, "Given the current time of day and weather, what is the likely color of the sky in Boston?")
        };

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }, kernel);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
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
        Assert.Equal("1", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("id").GetString());
        Assert.Equal("MyPlugin-GetCurrentWeather", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("function").GetProperty("name").GetString());

        var functionResult = messages[4];
        Assert.Equal("tool", functionResult.GetProperty("role").GetString());
        Assert.Equal("rainy", functionResult.GetProperty("content").GetString());
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsShouldSendMutatedChatHistoryToLLM()
    {
        // Arrange
        static void MutateChatHistory(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Remove the function call messages from the chat history to reduce token count.
            context.ChatHistory.RemoveRange(1, 2); // Remove the `Date` function call and function result messages.

            next(context);
        }

        var kernel = new Kernel();
        kernel.ImportPluginFromFunctions("MyPlugin", [KernelFunctionFactory.CreateFromMethod(() => "rainy", "GetCurrentWeather")]);
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(MutateChatHistory));

        using var firstResponse = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_single_function_call_test_response.txt")) };
        this._messageHandlerStub.ResponseQueue.Enqueue(firstResponse);

        using var secondResponse = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_test_response.txt")) };
        this._messageHandlerStub.ResponseQueue.Enqueue(secondResponse);

        var sut = new OpenAIChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClient);

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What time is it?"),
            new ChatMessageContent(AuthorRole.Assistant, [
                new FunctionCallContent("Date", "TimePlugin", "2")
            ]),
            new ChatMessageContent(AuthorRole.Tool, [
                new FunctionResultContent("Date",  "TimePlugin", "2", "rainy")
            ]),
            new ChatMessageContent(AuthorRole.Assistant, "08/06/2024 00:00:00"),
            new ChatMessageContent(AuthorRole.User, "Given the current time of day and weather, what is the likely color of the sky in Boston?")
        };

        // Act
        await foreach (var update in sut.GetStreamingChatMessageContentsAsync(chatHistory, new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }, kernel))
        {
        }

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
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
        Assert.Equal("1", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("id").GetString());
        Assert.Equal("MyPlugin-GetCurrentWeather", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("function").GetProperty("name").GetString());

        var functionResult = messages[4];
        Assert.Equal("tool", functionResult.GetProperty("role").GetString());
        Assert.Equal("rainy", functionResult.GetProperty("content").GetString());
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
        this._multiMessageHandlerStub.Dispose();
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

    private const string ChatCompletionResponse = """
        {
          "id": "chatcmpl-8IlRBQU929ym1EqAY2J4T7GGkW5Om",
          "object": "chat.completion",
          "created": 1699482945,
          "model": "gpt-3.5-turbo",
          "choices": [
            {
              "index": 0,
              "message": {
                "role": "assistant",
                "content": null,
                "tool_calls":[{
                    "id": "1",
                    "type": "function",
                    "function": {
                      "name": "TimePlugin-Date",
                      "arguments": "{}"
                    }
                  }
                ]
              },
              "finish_reason": "tool_calls"
            }
          ],
          "usage": {
            "prompt_tokens": 52,
            "completion_tokens": 1,
            "total_tokens": 53
          }
        }
        """;
}
