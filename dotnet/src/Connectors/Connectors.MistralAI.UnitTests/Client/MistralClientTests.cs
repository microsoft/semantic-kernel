// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.OpenApi.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
using Xunit;

namespace SemanticKernel.Connectors.MistralAI.UnitTests.Client;

/// <summary>
/// Unit tests for <see cref="MistralClient"/>.
/// </summary>
public sealed class MistralClientTests : MistralTestBase
{
    [Fact]
    public void ValidateRequiredArguments()
    {
        // Arrange
        // Act
        // Assert
        Assert.Throws<ArgumentException>(() => new MistralClient(string.Empty, new HttpClient(), "key"));
        Assert.Throws<ArgumentException>(() => new MistralClient("model", new HttpClient(), string.Empty));
#pragma warning disable CS8625 // Cannot convert null literal to non-nullable reference type.
        Assert.Throws<ArgumentNullException>(() => new MistralClient(null, new HttpClient(), "key"));
        Assert.Throws<ArgumentNullException>(() => new MistralClient("model", null, "key"));
        Assert.Throws<ArgumentNullException>(() => new MistralClient("model", new HttpClient(), null));
#pragma warning restore CS8625 // Cannot convert null literal to non-nullable reference type.
    }

    [Fact]
    public async Task ValidateChatMessageRequestAsync()
    {
        // Arrange
        var response = this.GetTestData("chat_completions_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", response);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-small-latest", this.HttpClient, "key");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { MaxTokens = 1024, Temperature = 0.9 };
        await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings);

        // Assert
        var request = this.DelegatingHandler.RequestContent;
        Assert.NotNull(request);
        var chatRequest = JsonSerializer.Deserialize<ChatCompletionRequest>(request);
        Assert.NotNull(chatRequest);
        Assert.Equal("mistral-small-latest", chatRequest.Model);
        Assert.Equal(1024, chatRequest.MaxTokens);
        Assert.Equal(0.9, chatRequest.Temperature);
        Assert.Single(chatRequest.Messages);
        Assert.Equal("user", chatRequest.Messages[0].Role);
        Assert.Equal("What is the best French cheese?", chatRequest.Messages[0].Content);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsAsync()
    {
        // Arrange
        var content = this.GetTestData("chat_completions_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this.HttpClient, "key");

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("I don't have a favorite condiment as I don't consume food or condiments. However, I can tell you that many people enjoy using ketchup, mayonnaise, hot sauce, soy sauce, or mustard as condiments to enhance the flavor of their meals. Some people also enjoy using herbs, spices, or vinegars as condiments. Ultimately, the best condiment is a matter of personal preference.", response[0].Content);
        Assert.Equal("mistral-tiny", response[0].ModelId);
        Assert.Equal(AuthorRole.Assistant, response[0].Role);
        Assert.NotNull(response[0].Metadata);
        Assert.Equal(7, response[0].Metadata?.Count);
    }

    [Fact]
    public async Task ValidateGenerateEmbeddingsAsync()
    {
        // Arrange
        var content = this.GetTestData("embeddings_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/embeddings", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this.HttpClient, "key");

        // Act
        List<string> data = ["Hello", "world"];
        var response = await client.GenerateEmbeddingsAsync(data, default);

        // Assert
        Assert.NotNull(response);
        Assert.Equal(2, response.Count);
        Assert.Equal(1024, response[0].Length);
        Assert.Equal(1024, response[1].Length);
    }

    [Fact]
    public async Task ValidateGetStreamingChatMessageContentsAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsBytes("chat_completions_streaming_response.txt");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this.HttpClient, "key");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };

        // Act
        var response = client.GetStreamingChatMessageContentsAsync(chatHistory, default);
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in response)
        {
            chunks.Add(chunk);
        };

        // Assert
        Assert.NotNull(response);
        Assert.Equal(124, chunks.Count);
        foreach (var chunk in chunks)
        {
            Assert.NotNull(chunk);
            Assert.Equal("mistral-tiny", chunk.ModelId);
            Assert.NotNull(chunk.Content);
            Assert.NotNull(chunk.Role);
            Assert.NotNull(chunk.Metadata);
        }
    }

    [Fact]
    public async Task ValidateChatHistoryFirstSystemOrUserMessageAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsBytes("chat_completions_streaming_response.txt");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this.HttpClient, "key");

        // First message in chat history must be a user or system message
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.Assistant, "What is the best French cheese?")
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(async () => await client.GetChatMessageContentsAsync(chatHistory, default));
    }

    [Fact]
    public async Task ValidateEmptyChatHistoryAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsBytes("chat_completions_streaming_response.txt");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this.HttpClient, "key");
        var chatHistory = new ChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(async () => await client.GetChatMessageContentsAsync(chatHistory, default));
    }

    [Fact]
    public async Task ValidateChatMessageRequestWithToolsAsync()
    {
        // Arrange
        var response = this.GetTestData("function_call_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", response);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-small-latest", this.HttpClient, "key");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };

        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.EnableKernelFunctions };

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        var request = this.DelegatingHandler.RequestContent;
        Assert.NotNull(request);
        var chatRequest = JsonSerializer.Deserialize<ChatCompletionRequest>(request);
        Assert.NotNull(chatRequest);
        Assert.Equal("auto", chatRequest.ToolChoice);
        Assert.NotNull(chatRequest.Tools);
        Assert.Single(chatRequest.Tools);
        Assert.NotNull(chatRequest.Tools[0].Function.Parameters);
        Assert.Equal(["location"], chatRequest.Tools[0].Function.Parameters?.Required);
        Assert.Equal("string", chatRequest.Tools[0].Function.Parameters?.Properties["location"].RootElement.GetProperty("type").GetString());
    }

    [Fact]
    public async Task ValidateGetStreamingChatMessageContentsWithToolsAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsBytes("chat_completions_streaming_function_call_response.txt");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-tiny", this.HttpClient, "key");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var response = client.GetStreamingChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in response)
        {
            chunks.Add(chunk);
        };

        // Assert
        Assert.NotNull(response);
        Assert.Equal(12, chunks.Count); // Test will loop until maximum use attempts is reached
        var request = this.DelegatingHandler.RequestContent;
        Assert.NotNull(request);
        var chatRequest = JsonSerializer.Deserialize<ChatCompletionRequest>(request);
        Assert.NotNull(chatRequest);
        Assert.Equal("auto", chatRequest.ToolChoice);
        Assert.NotNull(chatRequest.Tools);
        Assert.Single(chatRequest.Tools);
        Assert.NotNull(chatRequest.Tools[0].Function.Parameters);
        Assert.Equal(["location"], chatRequest.Tools[0].Function.Parameters?.Required);
        Assert.Equal("string", chatRequest.Tools[0].Function.Parameters?.Properties["location"].RootElement.GetProperty("type").GetString());
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithFunctionCallAsync()
    {
        // Arrange
        var functionCallContent = this.GetTestData("chat_completions_function_call_response.json");
        var functionCalledContent = this.GetTestData("chat_completions_function_called_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", functionCallContent, functionCalledContent);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-large-latest", this.HttpClient, "key");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("The weather in Paris is mostly cloudy with a temperature of 12°C. The wind speed is 11 KMPH and the humidity is at 48%.", response[0].Content);
        Assert.Equal("mistral-large-latest", response[0].ModelId);
        Assert.Equal(2, this.DelegatingHandler.SendAsyncCallCount);
        Assert.Equal(3, chatHistory.Count);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithFunctionCallNoneAsync()
    {
        // Arrange
        var content = this.GetTestData("chat_completions_function_call_none_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-large-latest", this.HttpClient, "key");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.NoKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("Sure, let me check the weather for you.\n\n[{\"name\": \"WeatherPlugin-GetWeather\", \"arguments\": {\"location\": \"Paris, 75\"}}}]", response[0].Content);
        Assert.Equal("mistral-large-latest", response[0].ModelId);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithFunctionCallRequiredAsync()
    {
        // Arrange
        var functionCallContent = this.GetTestData("chat_completions_function_call_response.json");
        var functionCalledContent = this.GetTestData("chat_completions_function_called_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", functionCallContent, functionCalledContent);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-large-latest", this.HttpClient, "key");

        var kernel = new Kernel();
        var plugin = kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.RequiredFunctions(plugin, true) };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("The weather in Paris is mostly cloudy with a temperature of 12°C. The wind speed is 11 KMPH and the humidity is at 48%.", response[0].Content);
        Assert.Equal("mistral-large-latest", response[0].ModelId);
        Assert.Equal(2, this.DelegatingHandler.SendAsyncCallCount);
        Assert.Equal(3, chatHistory.Count);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithFunctionInvocationFilterAsync()
    {
        // Arrange
        var functionCallContent = this.GetTestData("chat_completions_function_call_response.json");
        var functionCalledContent = this.GetTestData("chat_completions_function_called_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", functionCallContent, functionCalledContent);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-large-latest", this.HttpClient, "key");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        var invokedFunctions = new List<string>();
        var filter = new FakeFunctionFilter(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });
        kernel.FunctionInvocationFilters.Add(filter);

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("The weather in Paris is mostly cloudy with a temperature of 12°C. The wind speed is 11 KMPH and the humidity is at 48%.", response[0].Content);
        Assert.Equal("mistral-large-latest", response[0].ModelId);
        Assert.Equal(2, this.DelegatingHandler.SendAsyncCallCount);
        Assert.Equal(3, chatHistory.Count);
        Assert.Contains("GetWeather", invokedFunctions);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithAutoFunctionInvocationFilterTerminateAsync()
    {
        // Arrange
        var functionCallContent = this.GetTestData("chat_completions_function_call_response.json");
        var functionCalledContent = this.GetTestData("chat_completions_function_called_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", functionCallContent, functionCalledContent);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient("mistral-large-latest", this.HttpClient, "key");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        var invokedFunctions = new List<string>();
        var filter = new FakeAutoFunctionFilter(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
            context.Terminate = true;
        });
        kernel.AutoFunctionInvocationFilters.Add(filter);

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy", response[0].Content);
        Assert.Null(response[0].ModelId);
        Assert.Equal(1, this.DelegatingHandler.SendAsyncCallCount);
        Assert.Equal(3, chatHistory.Count);
        Assert.Contains("GetWeather", invokedFunctions);
    }

    [Theory]
    [InlineData("system", "System Content")]
    [InlineData("user", "User Content")]
    [InlineData("assistant", "Assistant Content")]
    public void ValidateToMistralChatMessages(string roleLabel, string content)
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var chatMessage = new ChatMessageContent()
        {
            Role = new AuthorRole(roleLabel),
            Content = content,
        };

        // Act
        var messages = client.ToMistralChatMessages(chatMessage, default);

        // Assert
        Assert.NotNull(messages);
        Assert.Single(messages);
    }

    [Fact]
    public void ValidateToMistralChatMessagesWithFunctionCallContent()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var content = new ChatMessageContent()
        {
            Role = AuthorRole.Assistant,
            Items = [new FunctionCallContent("GetWeather"), new FunctionCallContent("GetCurrentTime")],
        };

        // Act
        var messages = client.ToMistralChatMessages(content, default);

        // Assert
        Assert.NotNull(messages);
        Assert.Single(messages);
    }

    [Fact]
    public void ValidateToMistralChatMessagesWithFunctionResultContent()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var content = new ChatMessageContent()
        {
            Role = AuthorRole.Tool,
            Items = [new FunctionResultContent("12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy"), new FunctionResultContent("15:20:44")],
        };

        // Act
        var messages = client.ToMistralChatMessages(content, default);

        // Assert
        Assert.NotNull(messages);
        Assert.Equal(2, messages.Count);
    }

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
        ) => "12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy";
    }

    internal enum TemperatureUnit { Celsius, Fahrenheit }

    public class WidgetFactory
    {
        [KernelFunction]
        [Description("Creates a new widget of the specified type and colors")]
        public string CreateWidget([Description("The colors of the widget to be created")] WidgetColor[] widgetColors)
        {
            var colors = string.Join('-', widgetColors.Select(c => c.GetDisplayName()).ToArray());
            return $"Widget created with colors: {colors}";
        }
    }

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum WidgetColor
    {
        [Description("Use when creating a red item.")]
        Red,

        [Description("Use when creating a green item.")]
        Green,

        [Description("Use when creating a blue item.")]
        Blue
    }

    private sealed class FakeFunctionFilter(
        Func<FunctionInvocationContext, Func<FunctionInvocationContext, Task>, Task>? onFunctionInvocation = null) : IFunctionInvocationFilter
    {
        private readonly Func<FunctionInvocationContext, Func<FunctionInvocationContext, Task>, Task>? _onFunctionInvocation = onFunctionInvocation;

        public Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next) =>
            this._onFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }

    private sealed class FakeAutoFunctionFilter(
        Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? onAutoFunctionInvocation = null) : IAutoFunctionInvocationFilter
    {
        private readonly Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? _onAutoFunctionInvocation = onAutoFunctionInvocation;

        public Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next) =>
            this._onAutoFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }
}
