// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Azure.AI.Inference;
using Azure.Core.Pipeline;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureAIInference.UnitTests.Services;

public sealed class AzureAIInferenceChatCompletionServiceOpenTelemetryTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _multiMessageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;
    private readonly Mock<ILogger<AzureAIInferenceChatCompletionServiceOpenTelemetryTests>> _mockLogger;

    public AzureAIInferenceChatCompletionServiceOpenTelemetryTests()
    {
        this._multiMessageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._multiMessageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
        this._mockLogger = new Mock<ILogger<AzureAIInferenceChatCompletionServiceOpenTelemetryTests>>();
        this._mockLoggerFactory.Setup(lf => lf.CreateLogger(It.IsAny<string>())).Returns(this._mockLogger.Object);
        this._mockLogger.Setup(l => l.IsEnabled(It.IsAny<LogLevel>())).Returns(true);

        // Enable OpenTelemetry diagnostics for tests
        AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnostics", true);
    }

    [Fact]
    public async Task OpenTelemetryTracingIsEnabledForStreamingChatCompletionAsync()
    {
        // Arrange
        bool activityStarted = false;
        bool activityStopped = false;
        string? operationName = null;
        string modelId = "model";

        // Set up an ActivityListener to capture the activity events
        using var activityListener = new ActivityListener
        {
            ShouldListenTo = _ => true,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            ActivityStarted = activity =>
            {
                if (activity.OperationName.Contains($"chat {modelId}"))
                {
                    activityStarted = true;
                    operationName = activity.OperationName;
                }
            },
            ActivityStopped = activity =>
            {
                if (activity.OperationName.Contains($"chat {modelId}"))
                {
                    activityStopped = true;
                }
            }
        };

        ActivitySource.AddActivityListener(activityListener);

        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(StreamingChatCompletionResponse) }
        );

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddAzureAIInferenceChatCompletion(
            modelId: modelId,
            apiKey: "apiKey",
            endpoint: new Uri("https://localhost"),
            httpClient: this._httpClient);
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        await foreach (var content in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            // Process streaming content
        }

        // Assert
        Assert.True(activityStarted, "OpenTelemetry activity should have started for streaming");
        Assert.True(activityStopped, "OpenTelemetry activity should have stopped for streaming");
        Assert.NotNull(operationName);
        Assert.Contains($"chat {modelId}", operationName);
    }

    [Fact]
    public async Task OpenTelemetryConfigCallbackIsInvokedForStreamingAsync()
    {
        // Arrange
        bool configCallbackInvoked = false;

        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(StreamingChatCompletionResponse) }
        );

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddAzureAIInferenceChatCompletion(
            modelId: "model",
            apiKey: "apiKey",
            endpoint: new Uri("https://localhost"),
            httpClient: this._httpClient,
            openTelemetryConfig: _ => configCallbackInvoked = true);
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        await foreach (var content in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            // Process streaming content
        }

        // Assert
        Assert.True(configCallbackInvoked, "The OpenTelemetry config callback should have been invoked for streaming");
    }

    [Fact]
    public async Task OpenTelemetrySourceNameIsUsedForStreamingAsync()
    {
        // Arrange
        string customSourceName = "CustomSourceName";
        bool correctSourceNameUsed = false;

        // Set up an ActivityListener to capture the activity events
        using var activityListener = new ActivityListener
        {
            ShouldListenTo = activitySource => activitySource.Name == customSourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            ActivityStarted = activity => correctSourceNameUsed = true
        };

        ActivitySource.AddActivityListener(activityListener);

        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(StreamingChatCompletionResponse) }
        );

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddAzureAIInferenceChatCompletion(
            modelId: "model",
            apiKey: "apiKey",
            endpoint: new Uri("https://localhost"),
            httpClient: this._httpClient,
            openTelemetrySourceName: customSourceName);
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        await foreach (var content in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            // Process streaming content
        }

        // Assert
        Assert.True(correctSourceNameUsed, "The custom OpenTelemetry source name should have been used for streaming");
    }
    [Fact]
    public async Task OpenTelemetrySourceNameIsUsedWhenProvidedAsync()
    {
        // Arrange
        string customSourceName = "CustomSourceName";
        bool correctSourceNameUsed = false;

        // Set up an ActivityListener to capture the activity events
        using var activityListener = new ActivityListener
        {
            ShouldListenTo = activitySource => activitySource.Name == customSourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            ActivityStarted = activity => correctSourceNameUsed = true
        };

        ActivitySource.AddActivityListener(activityListener);

        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/chat_completion_response.json")) }
        );

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddAzureAIInferenceChatCompletion(
            modelId: "model",
            apiKey: "apiKey",
            endpoint: new Uri("https://localhost"),
            httpClient: this._httpClient,
            openTelemetrySourceName: customSourceName);
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.True(correctSourceNameUsed, "The custom OpenTelemetry source name should have been used");
    }

    [Fact]
    public async Task OpenTelemetryConfigCallbackIsInvokedAsync()
    {
        // Arrange
        bool configCallbackInvoked = false;

        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/chat_completion_response.json")) }
        );

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddAzureAIInferenceChatCompletion(
            modelId: "model",
            apiKey: "apiKey",
            endpoint: new Uri("https://localhost"),
            httpClient: this._httpClient,
            openTelemetryConfig: _ => configCallbackInvoked = true);
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.True(configCallbackInvoked, "The OpenTelemetry config callback should have been invoked");
    }

    [Fact]
    public async Task OpenTelemetrySourceNameAndConfigCanBeUsedTogetherAsync()
    {
        // Arrange
        string customSourceName = "CustomSourceName";
        bool correctSourceNameUsed = false;
        bool configCallbackInvoked = false;

        // Set up an ActivityListener to capture the activity events
        using var activityListener = new ActivityListener
        {
            ShouldListenTo = activitySource => activitySource.Name == customSourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            ActivityStarted = activity => correctSourceNameUsed = true
        };

        ActivitySource.AddActivityListener(activityListener);

        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/chat_completion_response.json")) }
        );

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddAzureAIInferenceChatCompletion(
            modelId: "model",
            apiKey: "apiKey",
            endpoint: new Uri("https://localhost"),
            httpClient: this._httpClient,
            openTelemetrySourceName: customSourceName,
            openTelemetryConfig: _ => configCallbackInvoked = true);
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.True(correctSourceNameUsed, "The custom OpenTelemetry source name should have been used");
        Assert.True(configCallbackInvoked, "The OpenTelemetry config callback should have been invoked");
    }

    [Fact]
    public async Task OpenTelemetryWorksWithTokenCredentialAsync()
    {
        // Arrange
        string customSourceName = "CustomSourceName";
        bool correctSourceNameUsed = false;
        bool configCallbackInvoked = false;

        // Set up an ActivityListener to capture the activity events
        using var activityListener = new ActivityListener
        {
            ShouldListenTo = activitySource => activitySource.Name == customSourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            ActivityStarted = activity => correctSourceNameUsed = true
        };

        ActivitySource.AddActivityListener(activityListener);

        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/chat_completion_response.json")) }
        );

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);

        // Use a mock TokenCredential
        var mockCredential = new Mock<Azure.Core.TokenCredential>();
        mockCredential.Setup(c => c.GetTokenAsync(It.IsAny<Azure.Core.TokenRequestContext>(), It.IsAny<System.Threading.CancellationToken>())).ReturnsAsync(new Azure.Core.AccessToken("mockToken", DateTimeOffset.UtcNow.AddHours(1)));

        builder.AddAzureAIInferenceChatCompletion(
            modelId: "model",
            credential: mockCredential.Object,
            endpoint: new Uri("https://localhost"),
            httpClient: this._httpClient,
            openTelemetrySourceName: customSourceName,
            openTelemetryConfig: _ => configCallbackInvoked = true);
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.True(correctSourceNameUsed, "The custom OpenTelemetry source name should have been used");
        Assert.True(configCallbackInvoked, "The OpenTelemetry config callback should have been invoked");
    }

    [Fact]
    public async Task OpenTelemetryWorksWithChatCompletionsClientAsync()
    {
        // Arrange
        string customSourceName = "CustomSourceName";
        bool correctSourceNameUsed = false;
        bool configCallbackInvoked = false;

        // Set up an ActivityListener to capture the activity events
        using var activityListener = new ActivityListener
        {
            ShouldListenTo = activitySource => activitySource.Name == customSourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            ActivityStarted = activity => correctSourceNameUsed = true
        };

        ActivitySource.AddActivityListener(activityListener);

        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/chat_completion_response.json")) }
        );

        // Create a mock ChatCompletionsClient
        var azureAIClient = new ChatCompletionsClient(new Uri("https://localhost"), new Azure.AzureKeyCredential("apiKey"), new Azure.AI.Inference.AzureAIInferenceClientOptions() { Transport = new HttpClientTransport(this._httpClient) });

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddAzureAIInferenceChatCompletion(
            modelId: "model",
            chatClient: azureAIClient,
            openTelemetrySourceName: customSourceName,
            openTelemetryConfig: _ => configCallbackInvoked = true);
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.True(configCallbackInvoked, "The OpenTelemetry config callback should have been invoked");
        Assert.True(correctSourceNameUsed, "The custom OpenTelemetry source name should have been used");
    }

    public void Dispose()
    {
        // Disable OpenTelemetry diagnostics after tests
        AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnostics", false);

        this._httpClient.Dispose();
        this._multiMessageHandlerStub.Dispose();
    }

    private const string StreamingChatCompletionResponse = """
        data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613","system_fingerprint":"fp_44709d6fcb","choices":[{"index":0,"delta":{"role":"assistant","content":"This"},"logprobs":null,"finish_reason":null}]}

        data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613","system_fingerprint":"fp_44709d6fcb","choices":[{"index":0,"delta":{"content":" is"},"logprobs":null,"finish_reason":null}]}

        data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613","system_fingerprint":"fp_44709d6fcb","choices":[{"index":0,"delta":{"content":" a"},"logprobs":null,"finish_reason":null}]}

        data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613","system_fingerprint":"fp_44709d6fcb","choices":[{"index":0,"delta":{"content":" test."},"logprobs":null,"finish_reason":null}]}

        data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613","system_fingerprint":"fp_44709d6fcb","choices":[{"index":0,"delta":{},"logprobs":null,"finish_reason":"stop"}]}

        data: [DONE]
        """;
}
