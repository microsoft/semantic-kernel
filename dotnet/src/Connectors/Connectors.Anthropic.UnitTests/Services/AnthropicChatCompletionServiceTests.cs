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
using Anthropic;
using Anthropic.Exceptions;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
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
        this._httpClient = new HttpClient(this._messageHandlerStub, false);

        // Setup mock logger factory to return a proper mock logger
        var mockLogger = new Mock<ILogger<AnthropicChatCompletionService>>();
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
        this._mockLoggerFactory
            .Setup(f => f.CreateLogger(It.IsAny<string>()))
            .Returns(mockLogger.Object);
    }

    #region Test Helpers

    /// <summary>
    /// Sets up a function calling scenario with multiple HTTP responses.
    /// M.E.AI's FunctionInvokingChatClient automatically processes tool calls, which requires
    /// multiple HTTP responses: one for the tool call, and one for the final response.
    /// </summary>
    /// <param name="responseFiles">Test data file names (without path) to queue as responses.</param>
    private void SetupFunctionCallScenario(params string[] responseFiles)
    {
        foreach (var file in responseFiles)
        {
            this._messageHandlerStub.ResponseQueue.Enqueue(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(File.ReadAllText($"./TestData/{file}"))
            });
        }
    }

    #endregion

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

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void ConstructorWithInvalidModelIdThrowsArgumentException(string? modelId)
    {
        // Act & Assert
        // ThrowIfNullOrWhiteSpace throws ArgumentNullException for null, ArgumentException for empty/whitespace
        Assert.ThrowsAny<ArgumentException>(() => new AnthropicChatCompletionService(modelId!, "test-api-key"));
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void ConstructorWithInvalidApiKeyThrowsArgumentException(string? apiKey)
    {
        // Act & Assert
        // ThrowIfNullOrWhiteSpace throws ArgumentNullException for null, ArgumentException for empty/whitespace
        Assert.ThrowsAny<ArgumentException>(() => new AnthropicChatCompletionService("claude-sonnet-4-20250514", apiKey!));
    }

    [Fact]
    public void ConstructorWithNullAnthropicClientThrowsArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AnthropicChatCompletionService("claude-sonnet-4-20250514", (AnthropicClient)null!));
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

    #region Endpoint Request Tests

    [Fact]
    public async Task ItUsesDefaultEndpointAsync()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert - Anthropic API endpoint should be the default
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        Assert.StartsWith("https://api.anthropic.com/", this._messageHandlerStub.RequestUri.ToString());
    }

    [Theory]
    [InlineData("https://custom.anthropic.com/")]
    [InlineData("https://localhost:8080/")]
    [InlineData("https://proxy.example.com/v1/")]
    public async Task ItUsesCustomEndpointWhenProvidedAsync(string customEndpoint)
    {
        // Arrange
        var service = new AnthropicChatCompletionService(
            "claude-sonnet-4-20250514",
            "test-api-key",
            baseUrl: new Uri(customEndpoint),
            httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert - Request should use the custom endpoint
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        Assert.StartsWith(customEndpoint, this._messageHandlerStub.RequestUri.ToString());
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

    // NOTE: Parameter tests (Temperature, MaxTokens, TopP, TopK, StopSequences, SystemMessage, Roles)
    // are consolidated in the "Request Parameters Tests" region below.

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
        // Note: With M.E.AI architecture, metadata structure changed.
        // Usage information is now in a "Usage" key as a UsageDetails object.
        Assert.NotNull(result[0].Metadata);
        Assert.True(result[0].Metadata!.ContainsKey("Usage"));
        var usage = result[0].Metadata!["Usage"] as Microsoft.Extensions.AI.UsageDetails;
        Assert.NotNull(usage);
        Assert.NotNull(usage!.InputTokenCount);
        Assert.NotNull(usage.OutputTokenCount);
    }

    // NOTE: GetChatMessageContentsAsyncWithMultipleMessagesAsync moved to Request Parameters Tests region
    // as GetChatMessageContentsAsyncSendsMultipleMessagesAsync

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
        this.SetupFunctionCallScenario(
            "chat_completion_tool_call_response.json",
            "final_response_after_tool_call.json");

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle?");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        // With M.E.AI architecture, the final response is returned after tool call processing.
        // The chat history will contain the intermediate messages including the tool call.
        Assert.NotNull(result);
        Assert.Single(result);

        // The final response should be text content (after the tool call was processed)
        Assert.Contains("weather", result[0].Content, StringComparison.OrdinalIgnoreCase);

        // Verify the chat history contains the function call from the first response
        var functionCalls = chatHistory.SelectMany(m => m.Items.OfType<FunctionCallContent>()).ToList();
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
        this.SetupFunctionCallScenario(
            "chat_completion_multiple_tool_calls_response.json",
            "final_response_after_tool_call.json");

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle and New York?");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);

        // Verify the chat history contains the function calls from the first response
        var functionCalls = chatHistory.SelectMany(m => m.Items.OfType<FunctionCallContent>()).ToList();
        Assert.Equal(2, functionCalls.Count);

        Assert.Equal("GetWeather", functionCalls[0].FunctionName);
        Assert.Equal("Seattle, WA", functionCalls[0].Arguments?["location"]?.ToString());

        Assert.Equal("GetWeather", functionCalls[1].FunctionName);
        Assert.Equal("New York, NY", functionCalls[1].Arguments?["location"]?.ToString());
    }

    [Fact]
    public async Task FunctionCallResponseShouldHaveUsageMetadataAsync()
    {
        // Arrange
        this.SetupFunctionCallScenario(
            "chat_completion_tool_call_response.json",
            "final_response_after_tool_call.json");

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather?");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        // The final response should have metadata with Usage information
        Assert.NotNull(result[0].Metadata);
        Assert.True(result[0].Metadata!.ContainsKey("Usage"));

        // Verify that the chat history contains the tool call from the first response
        var functionCalls = chatHistory.SelectMany(m => m.Items.OfType<FunctionCallContent>()).ToList();
        Assert.Single(functionCalls);
    }

    [Fact]
    public async Task FunctionCallResponseShouldAggregateTokenUsageAsync()
    {
        // Arrange
        // Response 1 (tool call): input_tokens=50, output_tokens=45
        // Response 2 (final): input_tokens=150, output_tokens=30
        // Expected aggregated: input=200, output=75
        this.SetupFunctionCallScenario(
            "chat_completion_tool_call_response.json",
            "final_response_after_tool_call.json");

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle?");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.NotNull(result[0].Metadata);
        Assert.True(result[0].Metadata!.ContainsKey("Usage"));

        var usage = result[0].Metadata!["Usage"] as Microsoft.Extensions.AI.UsageDetails;
        Assert.NotNull(usage);

        // M.E.AI FunctionInvokingChatClient aggregates token usage across all function calling iterations
        // Response 1: 50 input + 45 output, Response 2: 150 input + 30 output
        // Aggregated: 200 input, 75 output
        Assert.Equal(200, usage!.InputTokenCount);
        Assert.Equal(75, usage.OutputTokenCount);
    }

    [Fact]
    public async Task FunctionResultContentShouldBeSerializedToToolResultBlockAsync()
    {
        // Arrange - Create a chat history with a function call and its result
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle?");

        // Add assistant message with function call
        var assistantMessage = new ChatMessageContent(AuthorRole.Assistant, string.Empty);
        assistantMessage.Items.Add(new FunctionCallContent("GetWeather", "WeatherPlugin", "call_123", new KernelArguments { ["location"] = "Seattle" }));
        chatHistory.Add(assistantMessage);

        // Add tool result message
        var toolResultMessage = new ChatMessageContent(AuthorRole.Tool, [
            new FunctionResultContent(
                new FunctionCallContent("GetWeather", "WeatherPlugin", "call_123"),
                "Sunny, 72°F")
        ]);
        chatHistory.Add(toolResultMessage);

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert - Verify the request contains the tool result in Anthropic format
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);

        // Anthropic expects tool results in a user message with tool_result content blocks
        var requestJson = JsonDocument.Parse(requestBody);
        var messages = requestJson.RootElement.GetProperty("messages");

        // Find the message containing the tool result
        var hasToolResult = false;
        foreach (var message in messages.EnumerateArray())
        {
            if (message.TryGetProperty("content", out var content) && content.ValueKind == JsonValueKind.Array)
            {
                foreach (var contentBlock in content.EnumerateArray())
                {
                    if (contentBlock.TryGetProperty("type", out var typeElement) &&
                        typeElement.GetString() == "tool_result")
                    {
                        hasToolResult = true;
                        Assert.True(contentBlock.TryGetProperty("tool_use_id", out var toolUseId));
                        Assert.Equal("call_123", toolUseId.GetString());
                        break;
                    }
                }
            }
            if (hasToolResult)
            {
                break;
            }
        }

        Assert.True(hasToolResult, "Request should contain a tool_result content block");
    }

    #endregion

    #region Streaming Tests

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncReturnsContentAsync()
    {
        // Arrange - Use ReadAllBytesAsync + MemoryStream to avoid stream disposal issues
        // (the stream must remain open until the async enumerable is fully consumed)
        var fileContent = await File.ReadAllBytesAsync("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(new MemoryStream(fileContent))
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
        // Arrange - Use ReadAllBytesAsync + MemoryStream to avoid stream disposal issues
        var fileContent = await File.ReadAllBytesAsync("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(new MemoryStream(fileContent))
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

    /// <summary>
    /// Tests streaming with tool calls. Currently skipped due to Anthropic SDK bug.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>SDK Bug:</b> The Anthropic SDK's CreateStreaming method disposes the HttpResponseMessage
    /// before the IAsyncEnumerable is fully consumed, causing ObjectDisposedException.
    /// </para>
    /// <para>
    /// <b>Issue:</b> https://github.com/anthropics/anthropic-sdk-csharp/issues/80
    /// </para>
    /// <para>
    /// <b>TODO:</b> Once the SDK issue is fixed:
    /// 1. Remove the Skip attribute
    /// 2. Verify streaming tool calls return FunctionCallContent items
    /// 3. Add assertions for tool call ID, function name, and arguments
    /// 4. Consider adding a streaming equivalent of FunctionResultContentShouldBeSerializedToToolResultBlockAsync
    /// </para>
    /// </remarks>
    [Fact(Skip = "Anthropic SDK bug: CreateStreaming disposes HttpResponseMessage before IAsyncEnumerable is fully consumed. " +
                  "See: https://github.com/anthropics/anthropic-sdk-csharp/issues/80")]
    public async Task GetStreamingChatMessageContentsAsyncWithToolCallsReturnsContentAsync()
    {
        // Arrange
        var fileContent = await File.ReadAllBytesAsync("./TestData/chat_completion_streaming_tool_call_response.txt");
        var memoryStream = new MemoryStream(fileContent);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(memoryStream)
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

        // Assert - When SDK is fixed, add stronger assertions:
        // - Verify chunks contain FunctionCallContent items
        // - Verify tool call ID matches expected value
        // - Verify function name and arguments are correctly parsed
        Assert.NotEmpty(chunks);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncReturnsModelIdAsync()
    {
        // Arrange - Use ReadAllBytesAsync + MemoryStream to avoid stream disposal issues
        var fileContent = await File.ReadAllBytesAsync("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(new MemoryStream(fileContent))
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
        // Arrange - Use ReadAllBytesAsync + MemoryStream to avoid stream disposal issues
        var fileContent = await File.ReadAllBytesAsync("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(new MemoryStream(fileContent))
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

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncReturnsUsageMetadataAsync()
    {
        // Arrange - Use ReadAllBytesAsync + MemoryStream to avoid stream disposal issues
        var fileContent = await File.ReadAllBytesAsync("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(new MemoryStream(fileContent))
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

        // The final chunk(s) should contain usage metadata
        // Anthropic sends usage info in message_start and message_delta events
        var chunksWithMetadata = chunks.Where(c => c.Metadata is not null && c.Metadata.Count > 0).ToList();
        Assert.NotEmpty(chunksWithMetadata);

        // Verify at least one chunk has Usage information
        var hasUsage = chunks.Any(c =>
            c.Metadata is not null &&
            c.Metadata.TryGetValue("Usage", out var usage) &&
            usage is not null);
        Assert.True(hasUsage, "At least one streaming chunk should contain Usage metadata");
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
        // Arrange - Use ReadAllBytesAsync + MemoryStream to avoid stream disposal issues
        var fileContent = await File.ReadAllBytesAsync("./TestData/chat_completion_streaming_response.txt");
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(new MemoryStream(fileContent))
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
    public async Task GetChatMessageContentsAsyncWithEmptyChatHistoryThrowsBadRequestAsync()
    {
        // Arrange - M.E.AI handles empty chat history by sending an empty messages array
        // The Anthropic API will return an error, but the SDK handles this gracefully
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.BadRequest)
            {
                Content = new StringContent("{\"error\": {\"type\": \"invalid_request_error\", \"message\": \"messages: at least one message is required\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();

        // Act & Assert - Anthropic SDK throws AnthropicBadRequestException for empty messages
        await Assert.ThrowsAsync<AnthropicBadRequestException>(() => service.GetChatMessageContentsAsync(chatHistory));
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncWithEmptyChatHistoryThrowsAsync()
    {
        // Arrange - M.E.AI handles empty chat history by sending an empty messages array
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.BadRequest)
            {
                Content = new StringContent("{\"error\": {\"type\": \"invalid_request_error\", \"message\": \"messages: at least one message is required\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();

        // Act & Assert - Anthropic SDK throws AnthropicBadRequestException for empty messages
        await Assert.ThrowsAsync<AnthropicBadRequestException>(async () =>
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

        // Act & Assert - Anthropic SDK throws AnthropicUnauthorizedException for auth errors
        await Assert.ThrowsAsync<AnthropicUnauthorizedException>(() => service.GetChatMessageContentsAsync(chatHistory));
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

        // Act & Assert - Anthropic SDK throws AnthropicBadRequestException for bad requests
        await Assert.ThrowsAsync<AnthropicBadRequestException>(() => service.GetChatMessageContentsAsync(chatHistory));
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsAnthropicApiExceptionWithStatusCodeAsync()
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

        // Act & Assert - Anthropic SDK includes status code in AnthropicApiException
        var exception = await Assert.ThrowsAsync<AnthropicBadRequestException>(() => service.GetChatMessageContentsAsync(chatHistory));
        Assert.Equal(HttpStatusCode.BadRequest, exception.StatusCode);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsOnRateLimitAsync()
    {
        // Arrange
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage((HttpStatusCode)429)
            {
                Content = new StringContent("{\"error\": {\"type\": \"rate_limit_error\", \"message\": \"Rate limit exceeded. Please slow down.\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Anthropic SDK throws AnthropicRateLimitException for rate limit errors
        var exception = await Assert.ThrowsAsync<AnthropicRateLimitException>(() => service.GetChatMessageContentsAsync(chatHistory));
        Assert.Equal((HttpStatusCode)429, exception.StatusCode);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsOnServerErrorAsync()
    {
        // Arrange
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.InternalServerError)
            {
                Content = new StringContent("{\"error\": {\"type\": \"api_error\", \"message\": \"An internal server error occurred.\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Anthropic SDK throws Anthropic5xxException for server errors
        var exception = await Assert.ThrowsAsync<Anthropic5xxException>(() => service.GetChatMessageContentsAsync(chatHistory));
        Assert.Equal(HttpStatusCode.InternalServerError, exception.StatusCode);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsOnServiceUnavailableAsync()
    {
        // Arrange - HTTP 503 Service Unavailable (Anthropic overloaded)
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.ServiceUnavailable)
            {
                Content = new StringContent("{\"error\": {\"type\": \"overloaded_error\", \"message\": \"Anthropic's API is temporarily overloaded.\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Anthropic SDK throws Anthropic5xxException for 503 errors
        var exception = await Assert.ThrowsAsync<Anthropic5xxException>(() => service.GetChatMessageContentsAsync(chatHistory));
        Assert.Equal(HttpStatusCode.ServiceUnavailable, exception.StatusCode);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncThrowsOnRateLimitAsync()
    {
        // Arrange
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage((HttpStatusCode)429)
            {
                Content = new StringContent("{\"error\": {\"type\": \"rate_limit_error\", \"message\": \"Rate limit exceeded.\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Streaming should also throw on rate limit
        await Assert.ThrowsAsync<AnthropicRateLimitException>(async () =>
        {
            await foreach (var _ in service.GetStreamingChatMessageContentsAsync(chatHistory))
            {
            }
        });
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncThrowsOnServerErrorAsync()
    {
        // Arrange
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.InternalServerError)
            {
                Content = new StringContent("{\"error\": {\"type\": \"api_error\", \"message\": \"Internal server error.\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Streaming should also throw on server errors
        await Assert.ThrowsAsync<Anthropic5xxException>(async () =>
        {
            await foreach (var _ in service.GetStreamingChatMessageContentsAsync(chatHistory))
            {
            }
        });
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncThrowsOnUnauthorizedAsync()
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

        // Act & Assert - Streaming should also throw on authentication errors
        await Assert.ThrowsAsync<AnthropicUnauthorizedException>(async () =>
        {
            await foreach (var _ in service.GetStreamingChatMessageContentsAsync(chatHistory))
            {
            }
        });
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncThrowsOnServiceUnavailableAsync()
    {
        // Arrange - HTTP 503 Service Unavailable (Anthropic overloaded)
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.ServiceUnavailable)
            {
                Content = new StringContent("{\"error\": {\"type\": \"overloaded_error\", \"message\": \"Anthropic's API is temporarily overloaded.\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Streaming should also throw on 503 errors
        await Assert.ThrowsAsync<Anthropic5xxException>(async () =>
        {
            await foreach (var _ in service.GetStreamingChatMessageContentsAsync(chatHistory))
            {
            }
        });
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsOnForbiddenAsync()
    {
        // Arrange - HTTP 403 Forbidden (permission denied)
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.Forbidden)
            {
                Content = new StringContent("{\"error\": {\"type\": \"permission_error\", \"message\": \"Your API key does not have permission to use the specified resource.\"}}")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Anthropic SDK throws AnthropicForbiddenException for 403 errors
        var exception = await Assert.ThrowsAsync<AnthropicForbiddenException>(() => service.GetChatMessageContentsAsync(chatHistory));
        Assert.Equal(HttpStatusCode.Forbidden, exception.StatusCode);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsOnMalformedJsonResponseAsync()
    {
        // Arrange - API returns invalid JSON
        using var handler = new HttpMessageHandlerStub
        {
            ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent("This is not valid JSON {{{")
            }
        };
        using var httpClient = new HttpClient(handler, false);

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Anthropic SDK throws JsonException when parsing invalid JSON
        await Assert.ThrowsAsync<JsonException>(() => service.GetChatMessageContentsAsync(chatHistory));
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

    // Note: ModelId attribute test is already covered by AttributesShouldContainModelId in Attributes Tests region

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
    public async Task FunctionChoiceBehaviorAutoSendsToolsWithAutoChoiceAsync()
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

        // Assert - Parse JSON and verify structure
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestJson = JsonDocument.Parse(this._messageHandlerStub.RequestContent);

        // Verify tools array exists and contains our function
        Assert.True(requestJson.RootElement.TryGetProperty("tools", out var tools));
        Assert.Equal(JsonValueKind.Array, tools.ValueKind);
        Assert.True(tools.GetArrayLength() > 0);

        var toolNames = tools.EnumerateArray()
            .Where(t => t.TryGetProperty("name", out _))
            .Select(t => t.GetProperty("name").GetString())
            .ToList();
        // M.E.AI uses underscore separator for function names (TestPlugin_TestFunction)
        Assert.Contains("TestPlugin_TestFunction", toolNames);

        // Verify tool_choice is "auto"
        Assert.True(requestJson.RootElement.TryGetProperty("tool_choice", out var toolChoice));
        Assert.Equal("auto", toolChoice.GetProperty("type").GetString());
    }

    [Fact]
    public async Task FunctionChoiceBehaviorNoneSendsToolsWithNoneChoiceAsync()
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

        // Assert - Parse JSON and verify structure
        // FunctionChoiceBehavior.None() sends available functions to the model with tool_choice: "none".
        // The model receives the tool definitions but is instructed NOT to call any of them.
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestJson = JsonDocument.Parse(this._messageHandlerStub.RequestContent);

        // Verify tools array exists and contains our function
        Assert.True(requestJson.RootElement.TryGetProperty("tools", out var tools));
        Assert.Equal(JsonValueKind.Array, tools.ValueKind);

        var toolNames = tools.EnumerateArray()
            .Where(t => t.TryGetProperty("name", out _))
            .Select(t => t.GetProperty("name").GetString())
            .ToList();
        // M.E.AI uses underscore separator for function names (TestPlugin_TestFunction)
        Assert.Contains("TestPlugin_TestFunction", toolNames);

        // Verify tool_choice is "none"
        Assert.True(requestJson.RootElement.TryGetProperty("tool_choice", out var toolChoice));
        Assert.Equal("none", toolChoice.GetProperty("type").GetString());
    }

    [Fact]
    public async Task FunctionChoiceBehaviorRequiredSendsToolChoiceAnyAsync()
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

        // Assert - Parse JSON and verify structure
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestJson = JsonDocument.Parse(this._messageHandlerStub.RequestContent);

        // Verify tools array exists
        Assert.True(requestJson.RootElement.TryGetProperty("tools", out var tools));
        Assert.Equal(JsonValueKind.Array, tools.ValueKind);

        // Verify tool_choice is set (Anthropic uses "any" for required, meaning model must call a tool)
        Assert.True(requestJson.RootElement.TryGetProperty("tool_choice", out var toolChoice));
        Assert.Equal("any", toolChoice.GetProperty("type").GetString());
    }

    [Fact]
    public async Task NoFunctionChoiceBehaviorDoesNotSendToolsAsync()
    {
        // Arrange - No plugins, no FunctionChoiceBehavior
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // No settings with FunctionChoiceBehavior

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        await chatService.GetChatMessageContentsAsync(chatHistory, kernel: kernel);

        // Assert - No tools or tool_choice should be in the request
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestJson = JsonDocument.Parse(this._messageHandlerStub.RequestContent);

        Assert.False(requestJson.RootElement.TryGetProperty("tools", out _),
            "Request should not contain 'tools' when no FunctionChoiceBehavior is set");
        Assert.False(requestJson.RootElement.TryGetProperty("tool_choice", out _),
            "Request should not contain 'tool_choice' when no FunctionChoiceBehavior is set");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task FunctionChoiceBehaviorPassesAllowParallelCallsOptionAsync(bool allowParallelCalls)
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

        var options = new FunctionChoiceBehaviorOptions { AllowParallelCalls = allowParallelCalls };
        var settings = new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: options)
        };

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        await chatService.GetChatMessageContentsAsync(chatHistory, settings, kernel);

        // Assert - Anthropic uses "disable_parallel_tool_use" (inverted logic)
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestJson = JsonDocument.Parse(this._messageHandlerStub.RequestContent);

        Assert.True(requestJson.RootElement.TryGetProperty("tool_choice", out var toolChoice));

        // Anthropic uses disable_parallel_tool_use which is the inverse of AllowParallelCalls
        if (toolChoice.TryGetProperty("disable_parallel_tool_use", out var disableParallel))
        {
            Assert.Equal(!allowParallelCalls, disableParallel.GetBoolean());
        }
        else if (!allowParallelCalls)
        {
            // If AllowParallelCalls is false, disable_parallel_tool_use should be present and true
            Assert.Fail("Expected 'disable_parallel_tool_use' to be present when AllowParallelCalls is false");
        }
        // If AllowParallelCalls is true and disable_parallel_tool_use is not present, that's correct (default behavior)
    }

    [Fact]
    public async Task FunctionChoiceBehaviorAutoInvokesKernelFunctionAsync()
    {
        // Arrange - Set up multi-response scenario for function calling flow
        // Response 1: Model returns a tool call with M.E.AI-style function name (Plugin_Function)
        // Response 2: Model returns final text response after tool result
        // Note: Must use auto_invoke_tool_call_response.json which has "WeatherPlugin_GetWeather"
        // as the function name (M.E.AI uses underscore-separated plugin_function names)
        this.SetupFunctionCallScenario(
            "auto_invoke_tool_call_response.json",
            "final_response_after_tool_call.json");

        // Create a real kernel function that will be invoked
        var functionWasInvoked = false;
        var function = KernelFunctionFactory.CreateFromMethod(
            (string location) =>
            {
                functionWasInvoked = true;
                return $"The weather in {location} is sunny and 72°F";
            },
            "GetWeather",
            "Gets the current weather for a location");
        var plugin = KernelPluginFactory.CreateFromFunctions("WeatherPlugin", [function]);

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);
        builder.Services.AddSingleton<IChatCompletionService>(
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));
        var kernel = builder.Build();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle?");

        var settings = new AnthropicPromptExecutionSettings
        {
            // Auto with autoInvoke: true means the FunctionInvokingChatClient will
            // automatically call the kernel function and send the result back
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true)
        };

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        var result = await chatService.GetChatMessageContentsAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);

        // Verify the function was actually invoked by the kernel
        Assert.True(functionWasInvoked, "The kernel function should have been invoked during auto-invoke");

        // Verify the final response contains text (after tool call processing)
        Assert.NotNull(result[0].Content);
        Assert.NotEmpty(result[0].Content!);
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

        // Assert - Verify Anthropic image schema structure
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestJson = JsonDocument.Parse(this._messageHandlerStub.RequestContent);

        Assert.True(requestJson.RootElement.TryGetProperty("messages", out var messages));
        Assert.True(messages.GetArrayLength() > 0);

        var firstMessage = messages[0];
        Assert.True(firstMessage.TryGetProperty("content", out var content));
        Assert.True(content.ValueKind == JsonValueKind.Array);

        // Find the image content block
        var hasImageBlock = false;
        foreach (var block in content.EnumerateArray())
        {
            if (block.TryGetProperty("type", out var type) && type.GetString() == "image")
            {
                hasImageBlock = true;
                // Anthropic uses "source" with "type": "base64" for inline images
                Assert.True(block.TryGetProperty("source", out var source));
                Assert.Equal("base64", source.GetProperty("type").GetString());
                Assert.Equal("image/png", source.GetProperty("media_type").GetString());
                Assert.True(source.TryGetProperty("data", out _));
                break;
            }
        }
        Assert.True(hasImageBlock, "Request should contain an image content block");
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

        // Assert - Verify Anthropic image URL schema structure
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestJson = JsonDocument.Parse(this._messageHandlerStub.RequestContent);

        Assert.True(requestJson.RootElement.TryGetProperty("messages", out var messages));
        Assert.True(messages.GetArrayLength() > 0);

        var firstMessage = messages[0];
        Assert.True(firstMessage.TryGetProperty("content", out var content));
        Assert.True(content.ValueKind == JsonValueKind.Array);

        // Find the image content block
        var hasImageBlock = false;
        foreach (var block in content.EnumerateArray())
        {
            if (block.TryGetProperty("type", out var type) && type.GetString() == "image")
            {
                hasImageBlock = true;
                // Anthropic uses "source" with "type": "url" for URL-based images
                Assert.True(block.TryGetProperty("source", out var source));
                Assert.Equal("url", source.GetProperty("type").GetString());
                Assert.Equal("https://example.com/image.png", source.GetProperty("url").GetString());
                break;
            }
        }
        Assert.True(hasImageBlock, "Request should contain an image content block");
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithBinaryContentSendsPdfAsync()
    {
        // Arrange - Anthropic supports PDF documents via BinaryContent
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();

        // Create a minimal PDF-like byte array (just for testing serialization)
        // Real PDFs start with %PDF- header
        var pdfBytes = new byte[] { 0x25, 0x50, 0x44, 0x46, 0x2D }; // "%PDF-"
        var binaryContent = new BinaryContent(pdfBytes, "application/pdf");
        var textContent = new TextContent("Summarize this document.");

        var message = new ChatMessageContent(AuthorRole.User, [textContent, binaryContent]);
        chatHistory.Add(message);

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert - Verify Anthropic document schema structure
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestJson = JsonDocument.Parse(this._messageHandlerStub.RequestContent);

        Assert.True(requestJson.RootElement.TryGetProperty("messages", out var messages));
        Assert.True(messages.GetArrayLength() > 0);

        var firstMessage = messages[0];
        Assert.True(firstMessage.TryGetProperty("content", out var content));
        Assert.True(content.ValueKind == JsonValueKind.Array);

        // Find the document content block
        var hasDocumentBlock = false;
        foreach (var block in content.EnumerateArray())
        {
            if (block.TryGetProperty("type", out var type) && type.GetString() == "document")
            {
                hasDocumentBlock = true;
                // Anthropic uses "source" with "type": "base64" for inline documents
                Assert.True(block.TryGetProperty("source", out var source));
                Assert.Equal("base64", source.GetProperty("type").GetString());
                Assert.Equal("application/pdf", source.GetProperty("media_type").GetString());
                Assert.True(source.TryGetProperty("data", out _));
                break;
            }
        }
        Assert.True(hasDocumentBlock, "Request should contain a document content block for PDF");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetChatMessageContentsAsyncWithBinaryContentSendsDataCorrectlyAsync(bool useDataUri)
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();

        var pdfBytes = new byte[] { 0x25, 0x50, 0x44, 0x46, 0x2D, 0x31, 0x2E, 0x34 }; // "%PDF-1.4"
        var base64Data = Convert.ToBase64String(pdfBytes);

        BinaryContent binaryContent = useDataUri
            ? new BinaryContent($"data:application/pdf;base64,{base64Data}")
            : new BinaryContent(pdfBytes, "application/pdf");

        var message = new ChatMessageContent(AuthorRole.User, [new TextContent("Analyze this."), binaryContent]);
        chatHistory.Add(message);

        // Act
        await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);

        // Should contain base64-encoded PDF data
        Assert.Contains("application/pdf", requestBody);
        Assert.Contains(base64Data, requestBody);
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
        // Note: Temperature is converted from double to float in ChatOptions, causing precision loss
        // (0.7 double becomes 0.699999988079071 float). We verify the value is approximately correct.
        Assert.Contains("\"temperature\":", requestBody);
        var doc = System.Text.Json.JsonDocument.Parse(requestBody);
        var temperature = doc.RootElement.GetProperty("temperature").GetDouble();
        Assert.Equal(0.7, temperature, 5); // 5 decimal places precision
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
        // Note: TopP is converted from double to float in ChatOptions, causing precision loss.
        // We verify the value is approximately correct.
        Assert.Contains("\"top_p\":", requestBody);
        var doc = System.Text.Json.JsonDocument.Parse(requestBody);
        var topP = doc.RootElement.GetProperty("top_p").GetDouble();
        Assert.Equal(0.9, topP, 5); // 5 decimal places precision
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
    public async Task GetChatMessageContentsAsyncWithBothTemperatureAndTopPClearsTopPAsync()
    {
        // Arrange - Anthropic API does not allow both temperature and top_p simultaneously.
        // The connector should clear top_p when temperature is set.
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            Temperature = 0.7,
            TopP = 0.9
        };

        // Act
        await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"temperature\":", requestBody);
        Assert.DoesNotContain("\"top_p\"", requestBody);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncWithBothTemperatureAndTopPClearsTopPAsync()
    {
        // Arrange - Anthropic API does not allow both temperature and top_p simultaneously.
        // The connector should clear top_p when temperature is set.
        this._messageHandlerStub.ResponseQueue.Enqueue(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/chat_completion_streaming_response.txt"))
        });
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new AnthropicPromptExecutionSettings
        {
            Temperature = 0.5,
            TopP = 0.8
        };

        // Act
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in service.GetStreamingChatMessageContentsAsync(chatHistory, settings))
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);
        Assert.Contains("\"temperature\":", requestBody);
        Assert.DoesNotContain("\"top_p\"", requestBody);
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

    // NOTE: Text Generation Tests are in an earlier region (see GetTextContentsAsyncReturnsValidResponseAsync, etc.)
    // Duplicate region removed during code review.

    #region Logging Tests

    [Fact]
    public void ServiceCanBeCreatedWithLoggerFactory()
    {
        // Arrange - Must setup CreateLogger to return a valid logger
        var mockLogger = new Mock<ILogger<AnthropicChatCompletionService>>();
        var loggerFactory = new Mock<ILoggerFactory>();
        loggerFactory
            .Setup(f => f.CreateLogger(It.IsAny<string>()))
            .Returns(mockLogger.Object);

        // Act
        var service = new AnthropicChatCompletionService(
            "claude-sonnet-4-20250514",
            "test-api-key",
            loggerFactory: loggerFactory.Object);

        // Assert
        Assert.NotNull(service);
    }

    [Fact]
    public void ServiceCanBeCreatedWithNullLoggerFactory()
    {
        // Arrange & Act - Service should handle null logger factory gracefully
        var service = new AnthropicChatCompletionService(
            "claude-sonnet-4-20250514",
            "test-api-key",
            loggerFactory: null);

        // Assert
        Assert.NotNull(service);
    }

    #endregion

    #region Dispose Tests

    [Fact]
    public async Task GetChatMessageContentsAsyncThrowsAfterDispose()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        service.Dispose();

        // Assert
        await Assert.ThrowsAsync<ObjectDisposedException>(() => service.GetChatMessageContentsAsync(chatHistory));
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncThrowsAfterDispose()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act
        service.Dispose();

        // Assert
        await Assert.ThrowsAsync<ObjectDisposedException>(async () =>
        {
            await foreach (var _ in service.GetStreamingChatMessageContentsAsync(chatHistory))
            {
            }
        });
    }

    [Fact]
    public async Task GetTextContentsAsyncThrowsAfterDispose()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

        // Act
        service.Dispose();

        // Assert
        await Assert.ThrowsAsync<ObjectDisposedException>(() => service.GetTextContentsAsync("Hello"));
    }

    [Fact]
    public async Task GetStreamingTextContentsAsyncThrowsAfterDispose()
    {
        // Arrange
        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

        // Act
        service.Dispose();

        // Assert
        await Assert.ThrowsAsync<ObjectDisposedException>(async () =>
        {
            await foreach (var _ in service.GetStreamingTextContentsAsync("Hello"))
            {
            }
        });
    }

    #endregion

    #region Cancellation Token Tests

    [Fact]
    public async Task GetChatMessageContentsAsyncRespectsCancellationToken()
    {
        // Arrange
        using var cts = new CancellationTokenSource();
        cts.Cancel();

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Should throw OperationCanceledException when token is already cancelled
        await Assert.ThrowsAnyAsync<OperationCanceledException>(
            () => service.GetChatMessageContentsAsync(chatHistory, cancellationToken: cts.Token));
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncRespectsCancellationToken()
    {
        // Arrange
        using var cts = new CancellationTokenSource();
        cts.Cancel();

        var service = new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        // Act & Assert - Should throw OperationCanceledException when token is already cancelled
        await Assert.ThrowsAnyAsync<OperationCanceledException>(async () =>
        {
            await foreach (var _ in service.GetStreamingChatMessageContentsAsync(chatHistory, cancellationToken: cts.Token))
            {
            }
        });
    }

    #endregion

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
