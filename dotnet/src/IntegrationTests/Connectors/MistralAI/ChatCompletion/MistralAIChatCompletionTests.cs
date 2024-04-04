// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
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

    [Fact] // (Skip = "This test is for manual verification.")
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

    [Fact] // (Skip = "This test is for manual verification.")
    public async Task ValidateInvokeChatPromptAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var kernel = Kernel.CreateBuilder()
            .AddMistralChatCompletion(model!, apiKey!)
            .Build();

        const string ChatPrompt = @"
            <message role=""system"">Respond in French.</message>
            <message role=""user"">What is the best French cheese?</message>
        ";
        var chatSemanticFunction = kernel.CreateFunctionFromPrompt(ChatPrompt, this._executionSettings);

        // Act
        var response = await kernel.InvokeAsync(chatSemanticFunction);

        // Assert
        Assert.NotNull(response);
        Assert.False(string.IsNullOrEmpty(response.ToString()));
    }

    [Fact] // (Skip = "This test is for manual verification.")
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

    [Fact] // (Skip = "This test is for manual verification.")
    public async Task ValidateGetChatMessageContentsHasToolCallsResponseAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.EnableKernelFunctions };
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
        Assert.Equal("tool_calls", response[0].Metadata?["FinishReason"]);
    }

    [Fact] // (Skip = "This test is for manual verification.")
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

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
            ) => $"Weather in {location} is sunny and 18 celsius";
    }

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum TemperatureUnit { Celsius, Fahrenheit }
}
