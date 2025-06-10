// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.MistralAI;

/// <summary>
/// Integration tests for <see cref="MistralAIChatCompletionService"/>.
/// </summary>
public sealed class MistralAIChatCompletionTests : IDisposable
{
    private readonly ITestOutputHelper _output;
    private readonly IConfigurationRoot _configuration;
    private readonly MistralAIPromptExecutionSettings _executionSettings;
    private readonly HttpClientHandler _httpClientHandler;
    private readonly HttpMessageHandler _httpMessageHandler;
    private readonly HttpClient _httpClient;
    private bool _disposedValue;

    public MistralAIChatCompletionTests(ITestOutputHelper output)
    {
        this._output = output;

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

        this._httpClientHandler = new HttpClientHandler();
        this._httpMessageHandler = new LoggingHandler(this._httpClientHandler, this._output);
        this._httpClient = new HttpClient(this._httpMessageHandler);
    }
    private void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._httpClientHandler.Dispose();
                this._httpMessageHandler.Dispose();
                this._httpClient.Dispose();
            }
            this._disposedValue = true;
        }
    }

    public void Dispose()
    {
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);

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
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);

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
    public async Task ValidateGetChatMessageContentsWithImageAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ImageModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "Describe the image"),
            new ChatMessageContent(AuthorRole.User, [new ImageContent(new Uri("https://tripfixers.com/wp-content/uploads/2019/11/eiffel-tower-with-snow.jpeg"))])
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, this._executionSettings);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Contains("Paris", response[0].Content, System.StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Eiffel Tower", response[0].Content, System.StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Snow", response[0].Content, System.StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithImageDataUriAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ImageModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What's in this image?"),
            new ChatMessageContent(AuthorRole.User, [new ImageContent("data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA2ADYAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz/wAARCAAQABADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD5rooor8DP9oD/2Q==")])
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, this._executionSettings);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Contains("square", response[0].Content, System.StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithImageAndJsonFormatAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ImageModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);

        // Act
        var systemMessage = "Return the answer in a JSON object with the next structure: " +
                   "{\"elements\": [{\"element\": \"some name of element1\", " +
                   "\"description\": \"some description of element 1\"}, " +
                   "{\"element\": \"some name of element2\", \"description\": " +
                   "\"some description of element 2\"}]}";
        var chatHistory = new ChatHistory(systemMessage)
        {
            new ChatMessageContent(AuthorRole.User, "Describe the image"),
            new ChatMessageContent(AuthorRole.User, [new ImageContent(new Uri("https://tripfixers.com/wp-content/uploads/2019/11/eiffel-tower-with-snow.jpeg"))])
        };
        var executionSettings = new MistralAIPromptExecutionSettings
        {
            MaxTokens = 500,
            ResponseFormat = new { type = "json_object" },
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Contains("Paris", response[0].Content, System.StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Eiffel Tower", response[0].Content, System.StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Snow", response[0].Content, System.StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateInvokeChatPromptAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModelId"];
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
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);

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
        }

        // Assert
        Assert.NotNull(response);
        Assert.True(chunks.Count > 0);
        Assert.False(string.IsNullOrEmpty(content.ToString()));
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsHasToolCallsResponseAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);
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
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);
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
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);
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
        Assert.Contains("Paris", response[0].Content, System.StringComparison.Ordinal);
        Assert.Contains("12°C", response[0].Content, System.StringComparison.Ordinal);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithNoFunctionsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);
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
        Assert.Contains("weather", response[0].Content, System.StringComparison.Ordinal);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithAutoInvokeReturnsFunctionCallContentAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);
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
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);
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
        Assert.Contains("GetWeather", invokedFunctions);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetStreamingChatMessageContentsWithAutoInvokeAndFunctionFilterAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);

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

        StringBuilder content = new();

        await foreach (var update in service.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel))
        {
            if (!string.IsNullOrEmpty(update.Content))
            {
                content.Append(update.Content);
            }
        }

        // Assert
        Assert.NotNull(content);
        Assert.Contains("GetWeather", invokedFunctions);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithAutoInvokeAndFunctionInvocationFilterAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);
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
        Assert.Contains("Paris", response[0].Content, System.StringComparison.Ordinal);
        Assert.Contains("12°C", response[0].Content, System.StringComparison.Ordinal);
        Assert.Contains("GetWeather", invokedFunctions);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task ValidateGetChatMessageContentsWithAutoInvokeAndMultipleCallsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!, httpClient: this._httpClient);
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
        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "What is the weather temperature in Marseille?"));
        var result2 = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);

        // Assert
        Assert.NotNull(result2);
        Assert.Single(result2);
        Assert.Contains("Marseille", result2[0].Content, System.StringComparison.Ordinal);
        Assert.Contains("12°C", result2[0].Content, System.StringComparison.Ordinal);
    }

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
            ) => $"12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy\nLocation: {location}";
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

    private sealed class LoggingHandler(HttpMessageHandler innerHandler, ITestOutputHelper output) : DelegatingHandler(innerHandler)
    {
        private static readonly JsonSerializerOptions s_jsonSerializerOptions = new() { WriteIndented = true };

        private readonly ITestOutputHelper _output = output;

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Log the request details
            if (request.Content is not null)
            {
                var content = await request.Content.ReadAsStringAsync(cancellationToken);
                this._output.WriteLine("=== REQUEST ===");
                try
                {
                    string formattedContent = JsonSerializer.Serialize(JsonSerializer.Deserialize<JsonElement>(content), s_jsonSerializerOptions);
                    this._output.WriteLine(formattedContent);
                }
                catch (JsonException)
                {
                    this._output.WriteLine(content);
                }
                this._output.WriteLine(string.Empty);
            }

            // Call the next handler in the pipeline
            var response = await base.SendAsync(request, cancellationToken);

            if (response.Content is not null)
            {
                // Log the response details
                var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);
                this._output.WriteLine("=== RESPONSE ===");
                try
                {
                    string formattedContent = JsonSerializer.Serialize(JsonSerializer.Deserialize<JsonElement>(responseContent), s_jsonSerializerOptions);
                    this._output.WriteLine(formattedContent);
                }
                catch (JsonException)
                {
                    this._output.WriteLine(responseContent);
                }
                this._output.WriteLine(string.Empty);
            }

            return response;
        }
    }
}
