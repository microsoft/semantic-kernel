// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.ChatCompletion;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIChatCompletionService"/>
/// </summary>
public sealed class AzureOpenAIChatCompletionServiceTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AzureOpenAIChatCompletionServiceTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();

        var mockLogger = new Mock<ILogger>();

        mockLogger.Setup(l => l.IsEnabled(It.IsAny<LogLevel>())).Returns(true);

        this._mockLoggerFactory.Setup(l => l.CreateLogger(It.IsAny<string>())).Returns(mockLogger.Object);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithApiKeyWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithTokenCredentialWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var service = includeLoggerFactory ?
            new AzureOpenAIChatCompletionService("deployment", "https://endpoint", credentials, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIChatCompletionService("deployment", "https://endpoint", credentials, "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithOpenAIClientWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var client = new OpenAIClient("key");
        var service = includeLoggerFactory ?
            new AzureOpenAIChatCompletionService("deployment", client, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIChatCompletionService("deployment", client, "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Fact]
    public async Task GetTextContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json"))
        });

        // Act
        var result = await service.GetTextContentsAsync("Prompt");

        // Assert
        Assert.True(result.Count > 0);
        Assert.Equal("Test chat response", result[0].Text);

        var usage = result[0].Metadata?["Usage"] as CompletionsUsage;

        Assert.NotNull(usage);
        Assert.Equal(55, usage.PromptTokens);
        Assert.Equal(100, usage.CompletionTokens);
        Assert.Equal(155, usage.TotalTokens);
    }

    [Fact]
    public async Task GetChatMessageContentsWithEmptyChoicesThrowsExceptionAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("{\"id\":\"response-id\",\"object\":\"chat.completion\",\"created\":1704208954,\"model\":\"gpt-4\",\"choices\":[],\"usage\":{\"prompt_tokens\":55,\"completion_tokens\":100,\"total_tokens\":155},\"system_fingerprint\":null}")
        });

        // Act & Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => service.GetChatMessageContentsAsync([]));

        Assert.Equal("Chat completions not found", exception.Message);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(129)]
    public async Task GetChatMessageContentsWithInvalidResultsPerPromptValueThrowsExceptionAsync(int resultsPerPrompt)
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        var settings = new OpenAIPromptExecutionSettings { ResultsPerPrompt = resultsPerPrompt };

        // Act & Assert
        var exception = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => service.GetChatMessageContentsAsync([], settings));

        Assert.Contains("The value must be in range between", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task GetChatMessageContentsHandlesSettingsCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        var settings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 123,
            Temperature = 0.6,
            TopP = 0.5,
            FrequencyPenalty = 1.6,
            PresencePenalty = 1.2,
            ResultsPerPrompt = 5,
            Seed = 567,
            TokenSelectionBiases = new Dictionary<int, int> { { 2, 3 } },
            StopSequences = ["stop_sequence"]
        };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("User Message");
        chatHistory.AddSystemMessage("System Message");
        chatHistory.AddAssistantMessage("Assistant Message");

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json"))
        });

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        var requestContent = this._messageHandlerStub.RequestContents[0];

        Assert.NotNull(requestContent);

        var content = JsonSerializer.Deserialize<JsonElement>(Encoding.UTF8.GetString(requestContent));

        var messages = content.GetProperty("messages");

        var userMessage = messages[0];
        var systemMessage = messages[1];
        var assistantMessage = messages[2];

        Assert.Equal("user", userMessage.GetProperty("role").GetString());
        Assert.Equal("User Message", userMessage.GetProperty("content").GetString());

        Assert.Equal("system", systemMessage.GetProperty("role").GetString());
        Assert.Equal("System Message", systemMessage.GetProperty("content").GetString());

        Assert.Equal("assistant", assistantMessage.GetProperty("role").GetString());
        Assert.Equal("Assistant Message", assistantMessage.GetProperty("content").GetString());

        Assert.Equal(123, content.GetProperty("max_tokens").GetInt32());
        Assert.Equal(0.6, content.GetProperty("temperature").GetDouble());
        Assert.Equal(0.5, content.GetProperty("top_p").GetDouble());
        Assert.Equal(1.6, content.GetProperty("frequency_penalty").GetDouble());
        Assert.Equal(1.2, content.GetProperty("presence_penalty").GetDouble());
        Assert.Equal(5, content.GetProperty("n").GetInt32());
        Assert.Equal(567, content.GetProperty("seed").GetInt32());
        Assert.Equal(3, content.GetProperty("logit_bias").GetProperty("2").GetInt32());
        Assert.Equal("stop_sequence", content.GetProperty("stop")[0].GetString());
    }

    [Theory]
    [MemberData(nameof(ResponseFormats))]
    public async Task GetChatMessageContentsHandlesResponseFormatCorrectlyAsync(object responseFormat, string? expectedResponseType)
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        var settings = new OpenAIPromptExecutionSettings
        {
            ResponseFormat = responseFormat
        };

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json"))
        });

        // Act
        var result = await service.GetChatMessageContentsAsync([], settings);

        // Assert
        var requestContent = this._messageHandlerStub.RequestContents[0];

        Assert.NotNull(requestContent);

        var content = JsonSerializer.Deserialize<JsonElement>(Encoding.UTF8.GetString(requestContent));

        Assert.Equal(expectedResponseType, content.GetProperty("response_format").GetProperty("type").GetString());
    }

    [Theory]
    [MemberData(nameof(ToolCallBehaviors))]
    public async Task GetChatMessageContentsWorksCorrectlyAsync(ToolCallBehavior behavior)
    {
        // Arrange
        var kernel = Kernel.CreateBuilder().Build();
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = behavior };

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json"))
        });

        // Act
        var result = await service.GetChatMessageContentsAsync([], settings, kernel);

        // Assert
        Assert.True(result.Count > 0);
        Assert.Equal("Test chat response", result[0].Content);

        var usage = result[0].Metadata?["Usage"] as CompletionsUsage;

        Assert.NotNull(usage);
        Assert.Equal(55, usage.PromptTokens);
        Assert.Equal(100, usage.CompletionTokens);
        Assert.Equal(155, usage.TotalTokens);
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

        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient, this._mockLoggerFactory.Object);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_multiple_function_calls_test_response.json")) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json")) };

        this._messageHandlerStub.ResponsesToReturn = [response1, response2];

        // Act
        var result = await service.GetChatMessageContentsAsync([], settings, kernel);

        // Assert
        Assert.True(result.Count > 0);
        Assert.Equal("Test chat response", result[0].Content);

        Assert.Equal(2, functionCallCount);
    }

    [Fact]
    public async Task GetChatMessageContentsWithFunctionCallMaximumAutoInvokeAttemptsAsync()
    {
        // Arrange
        const int DefaultMaximumAutoInvokeAttempts = 5;
        const int AutoInvokeResponsesCount = 6;

        int functionCallCount = 0;

        var kernel = Kernel.CreateBuilder().Build();
        var function = KernelFunctionFactory.CreateFromMethod((string location) =>
        {
            functionCallCount++;
            return "Some weather";
        }, "GetCurrentWeather");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]));

        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient, this._mockLoggerFactory.Object);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        var responses = new List<HttpResponseMessage>();

        for (var i = 0; i < AutoInvokeResponsesCount; i++)
        {
            responses.Add(new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_single_function_call_test_response.json")) });
        }

        this._messageHandlerStub.ResponsesToReturn = responses;

        // Act
        var result = await service.GetChatMessageContentsAsync([], settings, kernel);

        // Assert
        Assert.Equal(DefaultMaximumAutoInvokeAttempts, functionCallCount);
    }

    [Fact]
    public async Task GetChatMessageContentsWithRequiredFunctionCallAsync()
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

        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient, this._mockLoggerFactory.Object);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.RequireFunction(openAIFunction, autoInvoke: true) };

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_single_function_call_test_response.json")) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json")) };

        this._messageHandlerStub.ResponsesToReturn = [response1, response2];

        // Act
        var result = await service.GetChatMessageContentsAsync([], settings, kernel);

        // Assert
        Assert.Equal(1, functionCallCount);

        var requestContents = this._messageHandlerStub.RequestContents;

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
    public async Task GetStreamingTextContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        using var stream = new MemoryStream(Encoding.UTF8.GetBytes(OpenAITestHelper.GetTestResponse("chat_completion_streaming_test_response.txt")));

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        });

        // Act & Assert
        await foreach (var chunk in service.GetStreamingTextContentsAsync("Prompt"))
        {
            Assert.Equal("Test chat streaming response", chunk.Text);
        }
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        using var stream = new MemoryStream(Encoding.UTF8.GetBytes(OpenAITestHelper.GetTestResponse("chat_completion_streaming_test_response.txt")));

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        });

        // Act & Assert
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync([]))
        {
            Assert.Equal("Test chat streaming response", chunk.Content);
        }
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

        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient, this._mockLoggerFactory.Object);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_streaming_multiple_function_calls_test_response.txt")) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_streaming_test_response.txt")) };

        this._messageHandlerStub.ResponsesToReturn = [response1, response2];

        // Act & Assert
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync([], settings, kernel))
        {
            Assert.Equal("Test chat streaming response", chunk.Content);
        }

        Assert.Equal(2, functionCallCount);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWithFunctionCallMaximumAutoInvokeAttemptsAsync()
    {
        // Arrange
        const int DefaultMaximumAutoInvokeAttempts = 5;
        const int AutoInvokeResponsesCount = 6;

        int functionCallCount = 0;

        var kernel = Kernel.CreateBuilder().Build();
        var function = KernelFunctionFactory.CreateFromMethod((string location) =>
        {
            functionCallCount++;
            return "Some weather";
        }, "GetCurrentWeather");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]));

        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient, this._mockLoggerFactory.Object);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        var responses = new List<HttpResponseMessage>();

        for (var i = 0; i < AutoInvokeResponsesCount; i++)
        {
            responses.Add(new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_streaming_single_function_call_test_response.txt")) });
        }

        this._messageHandlerStub.ResponsesToReturn = responses;

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

        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient, this._mockLoggerFactory.Object);
        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.RequireFunction(openAIFunction, autoInvoke: true) };

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_streaming_single_function_call_test_response.txt")) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_streaming_test_response.txt")) };

        this._messageHandlerStub.ResponsesToReturn = [response1, response2];

        // Act & Assert
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync([], settings, kernel))
        {
            Assert.Equal("Test chat streaming response", chunk.Content);
        }

        Assert.Equal(1, functionCallCount);

        var requestContents = this._messageHandlerStub.RequestContents;

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

        var service = new AzureOpenAIChatCompletionService("deployment", "https://endpoint", "api-key", "model-id", this._httpClient);
        var settings = new OpenAIPromptExecutionSettings() { ChatSystemPrompt = SystemMessage };

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json"))
        });

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => service);
        Kernel kernel = builder.Build();

        // Act
        var result = await kernel.InvokePromptAsync(Prompt, new(settings));

        // Assert
        Assert.Equal("Test chat response", result.ToString());

        var requestContentByteArray = this._messageHandlerStub.RequestContents[0];

        Assert.NotNull(requestContentByteArray);

        var requestContent = JsonSerializer.Deserialize<JsonElement>(Encoding.UTF8.GetString(requestContentByteArray));

        var messages = requestContent.GetProperty("messages");

        Assert.Equal(2, messages.GetArrayLength());

        Assert.Equal("This is test system message", messages[0].GetProperty("content").GetString());
        Assert.Equal("system", messages[0].GetProperty("role").GetString());

        Assert.Equal("This is test prompt", messages[1].GetProperty("content").GetString());
        Assert.Equal("user", messages[1].GetProperty("role").GetString());
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    public static TheoryData<ToolCallBehavior> ToolCallBehaviors => new()
    {
        ToolCallBehavior.EnableKernelFunctions,
        ToolCallBehavior.AutoInvokeKernelFunctions
    };

    public static TheoryData<object, string?> ResponseFormats => new()
    {
        { new FakeChatCompletionsResponseFormat(), null },
        { "json_object", "json_object" },
        { "text", "text" }
    };

    private sealed class FakeChatCompletionsResponseFormat : ChatCompletionsResponseFormat { }
}
