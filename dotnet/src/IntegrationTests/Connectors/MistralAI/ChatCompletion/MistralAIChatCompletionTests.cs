// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MistralAI;

/// <summary>
/// Integration tests for <see cref="MistralAIChatCompletionService"/>.
/// </summary>
public sealed class MistralAIChatCompletionTests
{
    private readonly IConfigurationRoot _configuration;
    private readonly MistralAIPromptExecutionSettings _executionSettings;

    public MistralAIChatCompletionTests()
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<MistralAIChatCompletionTests>()
            .Build();

        this._executionSettings = new MistralAIPromptExecutionSettings
        {
            MaxTokens = 500,
        };
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Respond in French."),
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, this._executionSettings);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.True(response[0].Content?.Length > 0);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithUsageAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Respond in French."),
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, this._executionSettings);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.True(response[0].Content?.Length > 0);
        Assert.NotNull(response[0].Metadata);
        Assert.True(response[0].Metadata?.ContainsKey("Usage"));
        var usage = response[0].Metadata?["Usage"] as MistralUsage;
        Assert.True(usage?.CompletionTokens > 0);
        Assert.True(usage?.PromptTokens > 0);
        Assert.True(usage?.TotalTokens > 0);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateInvokeChatPromptAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var kernel = Kernel.CreateBuilder()
            .AddMistralChatCompletion(model!, apiKey!)
            .Build();

        const string ChatPrompt = """
            <message role="system">Respond in French.</message>
            <message role="user">What is the best French cheese?</message>
        """;
        var chatSemanticFunction = kernel.CreateFunctionFromPrompt(ChatPrompt, this._executionSettings);

        // Act
        var response = await kernel.InvokeAsync(chatSemanticFunction);

        // Assert
        Assert.NotNull(response);
        Assert.False(string.IsNullOrEmpty(response.ToString()));
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetStreamingChatMessageContentsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Respond in French."),
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = service.GetStreamingChatMessageContentsAsync(chatHistory, this._executionSettings);
        var chunks = new List<StreamingChatMessageContent>();
        var content = new StringBuilder();
        await foreach (var chunk in response)
        {
            chunks.Add(chunk);
            content.Append(chunk.Content);
        };

        // Assert
        Assert.NotNull(response);
        Assert.True(chunks.Count > 0);
        Assert.False(string.IsNullOrEmpty(content.ToString()));
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsHasToolCallsResponseAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);
        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.EnableKernelFunctions };
        var response = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("tool_calls", response[0].Metadata?["FinishReason"]);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsHasRequiredToolCallResponseAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);
        var kernel = new Kernel();
        var plugin = kernel.Plugins.AddFromType<AnonymousPlugin>();

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.RequiredFunctions(plugin) };
        var response = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("tool_calls", response[0].Metadata?["FinishReason"]);
        Assert.Equal(2, response[0].Items.Count);
        Assert.True(response[0].Items[1] is FunctionCallContent);
        Assert.Equal("DoSomething", ((FunctionCallContent)response[0].Items[1]).FunctionName);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithAutoInvokeAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Contains("sunny", response[0].Content, System.StringComparison.Ordinal);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithNoFunctionsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.NoKernelFunctions };
        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Contains("GetWeather", response[0].Content, System.StringComparison.Ordinal);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithAutoInvokeReturnsFunctionCallContentAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal(3, chatHistory.Count);
        Assert.Equal(2, chatHistory[1].Items.Count);
        Assert.True(chatHistory[1].Items[1] is FunctionCallContent);
        Assert.Equal("GetWeather", ((FunctionCallContent)chatHistory[1].Items[1]).FunctionName);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithAutoInvokeAndFunctionFilterAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);
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
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var response = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Contains("sunny", response[0].Content, System.StringComparison.Ordinal);
        Assert.Contains("GetWeather", invokedFunctions);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithAutoInvokeAndFunctionInvocationFilterAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);
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
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var response = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.StartsWith("Weather in Paris", response[0].Content);
        Assert.EndsWith("is sunny and 18 Celsius", response[0].Content);
        Assert.Contains("GetWeather", invokedFunctions);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithAutoInvokeAndMultipleCallsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);
        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var result1 = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);
        chatHistory.AddRange(result1);
        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "What is the weather like in Marseille?"));
        var result2 = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        Assert.NotNull(result2);
        Assert.Single(result2);
        Assert.Contains("Marseille", result2[0].Content);
        Assert.Contains("sunny", result2[0].Content);
    }

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
            ) => $"Weather in {location} is sunny and 18 Celsius";
    }

    public sealed class AnonymousPlugin
    {
        [KernelFunction]
        public string DoSomething() => "Weather at location is sunny and 18 Celsius";
    }

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum TemperatureUnit { Celsius, Fahrenheit }

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
