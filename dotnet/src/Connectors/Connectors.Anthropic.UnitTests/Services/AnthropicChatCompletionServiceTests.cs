// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Anthropic;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Connectors.Anthropic.Services;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="AnthropicChatCompletionService"/>.
/// </summary>
public sealed class AnthropicChatCompletionServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly MultipleHttpMessageHandlerStub _multiMessageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AnthropicChatCompletionServiceTests()
    {
        this._messageHandlerStub = new()
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(File.ReadAllText("./TestData/chat_completion_response.json"))
            }
        };
        this._multiMessageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    #region Constructor Tests

    [Fact]
    public void ConstructorWithApiKeyWorksCorrectly()
    {
        // Arrange & Act
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("claude-sonnet-4-20250514", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithApiKeyAndLoggerFactoryWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory
            ? new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", loggerFactory: this._mockLoggerFactory.Object)
            : new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("claude-sonnet-4-20250514", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ConstructorWithAnthropicClientShouldWork()
    {
        // Arrange
        string model = "claude-sonnet-4-20250514";
        var anthropicClient = new AnthropicClient(new global::Anthropic.Core.ClientOptions { APIKey = "test-api-key" });

        // Act
        var service = new AnthropicChatCompletionService(model, anthropicClient);

        // Assert
        Assert.NotNull(service);
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithAnthropicClientAndLoggerFactoryWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange
        var anthropicClient = new AnthropicClient(new global::Anthropic.Core.ClientOptions { APIKey = "test-api-key" });

        // Act
        var service = includeLoggerFactory
            ? new AnthropicChatCompletionService("claude-sonnet-4-20250514", anthropicClient, loggerFactory: this._mockLoggerFactory.Object)
            : new AnthropicChatCompletionService("claude-sonnet-4-20250514", anthropicClient);

        // Assert
        Assert.NotNull(service);
        Assert.Equal("claude-sonnet-4-20250514", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    #endregion

    #region Attributes Tests

    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string model = "claude-sonnet-4-20250514";
        var service = new AnthropicChatCompletionService(model, "test-api-key");

        // Assert
        Assert.Equal(model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void AttributesShouldContainEndpoint()
    {
        // Arrange & Act
        string model = "claude-sonnet-4-20250514";
        var service = new AnthropicChatCompletionService(model, "test-api-key");

        // Assert
        Assert.Equal("https://api.anthropic.com/", service.Attributes[AIServiceExtensions.EndpointKey]);
    }

    [Fact]
    public void AttributesShouldContainCustomEndpoint()
    {
        // Arrange & Act
        string model = "claude-sonnet-4-20250514";
        var customEndpoint = new Uri("https://custom.anthropic.endpoint/");
        var service = new AnthropicChatCompletionService(model, "test-api-key", baseUrl: customEndpoint);

        // Assert
        Assert.Equal(customEndpoint.ToString(), service.Attributes[AIServiceExtensions.EndpointKey]);
    }

    [Theory]
    [InlineData("https://localhost:1234/", "https://localhost:1234/")]
    [InlineData("https://localhost:8080/", "https://localhost:8080/")]
    [InlineData("https://custom.anthropic.com/", "https://custom.anthropic.com/")]
    [InlineData("https://custom.anthropic.com/v1", "https://custom.anthropic.com/v1")]
    public void AttributesShouldContainVariousCustomEndpoints(string endpointProvided, string expectedEndpoint)
    {
        // Arrange & Act
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", baseUrl: new Uri(endpointProvided));

        // Assert
        Assert.Equal(expectedEndpoint, service.Attributes[AIServiceExtensions.EndpointKey]);
    }

    #endregion

    #region GetChatMessageContentsAsync Tests

    [Fact]
    public async Task GetChatMessageContentsAsyncReturnsValidResponseAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, how are you?");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(AuthorRole.Assistant, result[0].Role);
        Assert.NotNull(result[0].Content);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncSendsCorrectRequestAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, how are you?");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("claude-sonnet-4-20250514", requestBody);
        Assert.Contains("Hello, how are you?", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithSettingsSendsCorrectParametersAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        var settings = new AnthropicPromptExecutionSettings
        {
            Temperature = 0.7,
            MaxTokens = 1024,
            TopK = 40
        };

        // Act
        await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"temperature\":0.7", requestBody);
        Assert.Contains("\"max_tokens\":1024", requestBody);
        Assert.Contains("\"top_k\":40", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithSystemMessageSendsSystemPromptAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("You are a helpful assistant.");
        chatHistory.AddUserMessage("Hello");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("You are a helpful assistant.", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithTopPSendsTopPAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        var settings = new AnthropicPromptExecutionSettings
        {
            TopP = 0.9
        };

        // Act
        await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"top_p\":0.9", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithStopSequencesSendsStopSequencesAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        var settings = new AnthropicPromptExecutionSettings
        {
            StopSequences = ["END", "STOP"]
        };

        // Act
        await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("stop_sequences", requestBody);
        Assert.Contains("END", requestBody);
        Assert.Contains("STOP", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncShouldHaveModelIdDefinedAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(result[0].ModelId);
        Assert.Equal("claude-sonnet-4-20250514", result[0].ModelId);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncReturnsMetadataAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(result[0].Metadata);
        Assert.True(result[0].Metadata!.ContainsKey("Id"));
        Assert.True(result[0].Metadata!.ContainsKey("StopReason"));
        Assert.True(result[0].Metadata!.ContainsKey("InputTokens"));
        Assert.True(result[0].Metadata!.ContainsKey("OutputTokens"));
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithMultipleMessagesAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi there!");
        chatHistory.AddUserMessage("How are you?");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("Hello", requestBody);
        Assert.Contains("Hi there!", requestBody);
        Assert.Contains("How are you?", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithMultipleSystemMessagesAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("You are a helpful assistant.");
        chatHistory.AddSystemMessage("Always be polite.");
        chatHistory.AddUserMessage("Hello");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        // Both system messages should be concatenated
        Assert.Contains("You are a helpful assistant.", requestBody);
        Assert.Contains("Always be polite.", requestBody);
    }

    #endregion

    #region Function Calling Tests

    [Fact]
    public async Task FunctionCallsShouldBePropagatedViaChatMessageItemsAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/chat_completion_tool_call_response.json"))
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle?");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);

        // Should have text content and function call
        var functionCalls = result[0].Items.OfType<FunctionCallContent>().ToList();
        Assert.Single(functionCalls);

        var functionCall = functionCalls[0];
        Assert.Equal("GetWeather", functionCall.FunctionName);
        Assert.Equal("toolu_01A09q90qw90lq917835lq", functionCall.Id);
        Assert.NotNull(functionCall.Arguments);
        Assert.Equal("Seattle, WA", functionCall.Arguments["location"]?.ToString());
    }

    [Fact]
    public async Task MultipleFunctionCallsShouldBePropagatedViaChatMessageItemsAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/chat_completion_multiple_tool_calls_response.json"))
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle and New York?");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);

        var functionCalls = result[0].Items.OfType<FunctionCallContent>().ToList();
        Assert.Equal(2, functionCalls.Count);

        Assert.Equal("GetWeather", functionCalls[0].FunctionName);
        Assert.Equal("Seattle, WA", functionCalls[0].Arguments?["location"]?.ToString());

        Assert.Equal("GetWeather", functionCalls[1].FunctionName);
        Assert.Equal("New York, NY", functionCalls[1].Arguments?["location"]?.ToString());
    }

    [Fact]
    public async Task FunctionCallResponseShouldHaveToolUseStopReasonAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/chat_completion_tool_call_response.json"))
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather?");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(result[0].Metadata);
        Assert.Equal("ToolUse", result[0].Metadata!["StopReason"]);
        Assert.Equal("tool_calls", result[0].Metadata!["FinishReason"]);
    }

    #endregion

    #region Streaming Tests

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncReturnsContentAsync()
    {
        // Arrange
        using var stream = File.OpenRead("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotEmpty(chunks);
        Assert.All(chunks, c => Assert.Equal(AuthorRole.Assistant, c.Role));
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncWithSettingsAsync()
    {
        // Arrange
        using var stream = File.OpenRead("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        var settings = new AnthropicPromptExecutionSettings
        {
            Temperature = 0.5,
            MaxTokens = 500
        };

        // Act
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync(chatHistory, settings))
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotEmpty(chunks);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncWithToolCallsReturnsContentAsync()
    {
        // Arrange
        using var stream = File.OpenRead("./TestData/chat_completion_streaming_tool_call_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather?");

        // Act
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotEmpty(chunks);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncReturnsModelIdAsync()
    {
        // Arrange
        using var stream = File.OpenRead("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotEmpty(chunks);
        Assert.All(chunks, c => Assert.Equal("claude-sonnet-4-20250514", c.ModelId));
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncReturnsChunksWithContentAsync()
    {
        // Arrange
        using var stream = File.OpenRead("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotEmpty(chunks);
        // At least some chunks should have text content
        var combinedContent = string.Join("", chunks.Select(c => c.Content ?? ""));
        Assert.NotEmpty(combinedContent);
    }

    #endregion

    #region Text Generation Tests

    [Fact]
    public async Task GetTextContentsAsyncReturnsValidResponseAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

        // Act
        var result = await service.GetTextContentsAsync("Hello, how are you?");

        // Assert
        Assert.NotNull(result);
        Assert.NotEmpty(result);
    }

    [Fact]
    public async Task GetTextContentsAsyncShouldHaveModelIdDefinedAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

        // Act
        var result = await service.GetTextContentsAsync("Hello");

        // Assert
        Assert.NotNull(result[0].ModelId);
        Assert.Equal("claude-sonnet-4-20250514", result[0].ModelId);
    }

    [Fact]
    public async Task GetStreamingTextContentsAsyncReturnsContentAsync()
    {
        // Arrange
        using var stream = File.OpenRead("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

        // Act
        var chunks = new List<Microsoft.SemanticKernel.StreamingTextContent>();
        await foreach (var chunk in service.GetStreamingTextContentsAsync("Hello"))
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotEmpty(chunks);
    }

    #endregion

    #region Error Handling Tests

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsOnEmptyChatHistoryAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() => service.GetChatMessageContentsAsync(chatHistory));
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncThrowsOnEmptyChatHistoryAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(async () =>
        {
            await foreach (var _ in service.GetStreamingChatMessageContentsAsync(chatHistory))
            {
            }
        });
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsOnUnauthorizedAsync()
    {
        // Arrange
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.Unauthorized)
            {
                Content = new StringContent("{\"error\": {\"type\": \"authentication_error\", \"message\": \"Invalid API key\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "invalid-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Anthropic SDK wraps errors in HttpOperationException
        await Assert.ThrowsAsync<HttpOperationException>(() => service.GetChatMessageContentsAsync(chatHistory));
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsOnBadRequestAsync()
    {
        // Arrange
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.BadRequest)
            {
                Content = new StringContent("{\"error\": {\"type\": \"invalid_request_error\", \"message\": \"Invalid request\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Anthropic SDK wraps errors in HttpOperationException
        await Assert.ThrowsAsync<HttpOperationException>(() => service.GetChatMessageContentsAsync(chatHistory));
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsHttpOperationExceptionWithStatusCodeAsync()
    {
        // Arrange
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.BadRequest)
            {
                Content = new StringContent("{\"error\": {\"type\": \"invalid_request_error\", \"message\": \"Invalid request\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert
        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => service.GetChatMessageContentsAsync(chatHistory));
        Assert.Equal(HttpStatusCode.BadRequest, exception.StatusCode);
    }

    #endregion

    #region IChatCompletionService Interface Tests

    [Fact]
    public void ServiceImplementsIChatCompletionService()
    {
        // Arrange & Act
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key");

        // Assert
        Assert.IsAssignableFrom<IChatCompletionService>(service);
    }

    [Fact]
    public void ServiceImplementsITextGenerationService()
    {
        // Arrange & Act
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key");

        // Assert
        Assert.IsAssignableFrom<Microsoft.SemanticKernel.TextGeneration.ITextGenerationService>(service);
    }

    [Fact]
    public void ServiceAttributesContainModelId()
    {
        // Arrange & Act
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key");

        // Assert
        Assert.True(service.Attributes.ContainsKey(AIServiceExtensions.ModelIdKey));
        Assert.Equal("claude-sonnet-4-20250514", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ServiceAttributesAreReadOnly()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key");

        // Act & Assert
        Assert.IsAssignableFrom<IReadOnlyDictionary<string, object?>>(service.Attributes);
    }

    #endregion

    #region Kernel Integration Tests

    [Fact]
    public async Task ServiceCanBeUsedWithKernelAsync()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        var result = await chatService.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
    }

    [Fact]
    public async Task ServiceCanBeUsedWithInvokePromptAsync()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));
        var kernel = builder.Build();

        // Act
        var result = await kernel.InvokePromptAsync("Hello");

        // Assert
        Assert.NotNull(result);
    }

    [Fact]
    public async Task ServiceCanBeUsedWithPromptExecutionSettingsAsync()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));
        var kernel = builder.Build();

        var settings = new AnthropicPromptExecutionSettings
        {
            Temperature = 0.7,
            MaxTokens = 1024
        };

        // Act
        var result = await kernel.InvokePromptAsync("Hello", new(settings));

        // Assert
        Assert.NotNull(result);
    }

    #endregion

    #region FunctionChoiceBehavior Tests

    [Fact]
    public async Task FunctionChoiceBehaviorAutoSendsToolsAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "result", "TestFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("TestPlugin", [function]);

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);
        builder.Services.AddSingleton<IChatCompletionService>(
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        await chatService.GetChatMessageContentsAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("tools", requestBody);
        Assert.Contains("TestFunction", requestBody);
    }

    [Fact]
    public async Task FunctionChoiceBehaviorNoneSendsNoToolsAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "result", "TestFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("TestPlugin", [function]);

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);
        builder.Services.AddSingleton<IChatCompletionService>(
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.None()
        };

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        await chatService.GetChatMessageContentsAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.DoesNotContain("tools", requestBody);
    }

    [Fact]
    public async Task FunctionChoiceBehaviorRequiredSendsToolChoiceAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "result", "TestFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("TestPlugin", [function]);

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);
        builder.Services.AddSingleton<IChatCompletionService>(
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Required()
        };

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        await chatService.GetChatMessageContentsAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("tools", requestBody);
        Assert.Contains("tool_choice", requestBody);
    }

    #endregion

    #region Multimodal Tests

    [Fact]
    public async Task GetChatMessageContentsAsyncWithImageContentSendsImageAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();

        // Create a message with image content
        var imageBytes = new byte[] { 0x89, 0x50, 0x4E, 0x47 }; // PNG header bytes
        var imageContent = new ImageContent(imageBytes, "image/png");
        var textContent = new TextContent("What's in this image?");

        var message = new ChatMessageContent(AuthorRole.User, [textContent, imageContent]);
        chatHistory.Add(message);

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("image", requestBody);
        Assert.Contains("base64", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithImageUrlSendsImageAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();

        // Create a message with image URL content
        var imageContent = new ImageContent(new Uri("https://example.com/image.png"));
        var textContent = new TextContent("What's in this image?");

        var message = new ChatMessageContent(AuthorRole.User, [textContent, imageContent]);
        chatHistory.Add(message);

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("image", requestBody);
        Assert.Contains("url", requestBody);
    }

    #endregion

    #region Model Tests

    [Fact]
    public async Task GetChatMessageContentsAsyncUsesConstructorModelIdAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("claude-sonnet-4-20250514", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithDifferentModelUsesConstructorModelAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-3-haiku-20240307", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("claude-3-haiku-20240307", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncReturnsCorrectModelIdInResponseAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.Single(result);
        Assert.Equal("claude-sonnet-4-20250514", result[0].ModelId);
    }

    #endregion

    #region Request Parameters Tests

    [Fact]
    public async Task GetChatMessageContentsAsyncSendsTemperatureAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            Temperature = 0.7
        };

        // Act
        await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"temperature\":0.7", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncSendsMaxTokensAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            MaxTokens = 2048
        };

        // Act
        await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"max_tokens\":2048", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncSendsTopPAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            TopP = 0.9
        };

        // Act
        await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"top_p\":0.9", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncSendsTopKAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            TopK = 50
        };

        // Act
        await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"top_k\":50", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncSendsStopSequencesAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            StopSequences = ["END", "STOP"]
        };

        // Act
        await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("stop_sequences", requestBody);
        Assert.Contains("END", requestBody);
        Assert.Contains("STOP", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncSendsSystemPromptAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("You are a helpful assistant.");
        chatHistory.AddUserMessage("Hello");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("system", requestBody);
        Assert.Contains("You are a helpful assistant.", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncSendsMultipleMessagesAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("First message");
        chatHistory.AddAssistantMessage("First response");
        chatHistory.AddUserMessage("Second message");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("First message", requestBody);
        Assert.Contains("First response", requestBody);
        Assert.Contains("Second message", requestBody);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncSendsCorrectRolesAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("User message");
        chatHistory.AddAssistantMessage("Assistant message");
        chatHistory.AddUserMessage("Another user message");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"role\":\"user\"", requestBody);
        Assert.Contains("\"role\":\"assistant\"", requestBody);
    }

    #endregion

    #region Text Generation Tests

    [Fact]
    public async Task GetTextContentsAsyncReturnsTextContentAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

        // Act
        var result = await service.GetTextContentsAsync("Hello");

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.NotEmpty(result[0].Text!);
    }

    [Fact]
    public async Task GetStreamingTextContentsAsyncReturnsTextContentAsync()
    {
        // Arrange
        using var stream = File.OpenRead("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

        // Act
        var chunks = new List<StreamingTextContent>();
        await foreach (var chunk in service.GetStreamingTextContentsAsync("Hello"))
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotEmpty(chunks);
    }

    #endregion

    #region Logging Tests

    [Fact]
    public void ServiceCanBeCreatedWithLoggerFactory()
    {
        // Arrange
        var loggerFactory = new Mock<ILoggerFactory>();

        // Act
        var service = new AnthropicChatCompletionService(
            "claude-sonnet-4-20250514",
            "test-api-key",
            loggerFactory: loggerFactory.Object);

        // Assert
        Assert.NotNull(service);
    }

    #endregion

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
        this._multiMessageHandlerStub.Dispose();
    }
}
