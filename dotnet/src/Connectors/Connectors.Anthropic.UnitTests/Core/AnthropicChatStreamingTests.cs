// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core.Models;
using Microsoft.SemanticKernel.Http;
using SemanticKernel.Connectors.Anthropic.UnitTests.Utils;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Core;

/// <summary>
/// Test for <see cref="AnthropicClient"/>
/// </summary>
public sealed class AnthropicChatStreamingTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string ChatTestDataFilePath = "./TestData/chat_stream_response.txt";

    public AnthropicChatStreamingTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(ChatTestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldSetStreamTrueInRequestContentAsync()
    {
        // Arrange
        string modelId = "fake-model234";
        var client = this.CreateChatCompletionClient(modelId: modelId);
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        AnthropicRequest? request = JsonSerializer.Deserialize<AnthropicRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.True(request.Stream);
    }

    [Fact]
    public async Task ShouldPassModelIdToRequestContentAsync()
    {
        // Arrange
        string modelId = "fake-model234";
        var client = this.CreateChatCompletionClient(modelId: modelId);
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        AnthropicRequest? request = JsonSerializer.Deserialize<AnthropicRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Contains(modelId, request.ModelId, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldContainRolesInRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        AnthropicRequest? request = JsonSerializer.Deserialize<AnthropicRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Collection(request.Messages,
            item => Assert.Equal(chatHistory[1].Role, item.Role),
            item => Assert.Equal(chatHistory[2].Role, item.Role),
            item => Assert.Equal(chatHistory[3].Role, item.Role));
    }

    [Fact]
    public async Task ShouldContainMessagesInRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        AnthropicRequest? request = JsonSerializer.Deserialize<AnthropicRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Collection(request.Messages,
            item => Assert.Equal(chatHistory[1].Content, GetTextFrom(item.Contents[0])),
            item => Assert.Equal(chatHistory[2].Content, GetTextFrom(item.Contents[0])),
            item => Assert.Equal(chatHistory[3].Content, GetTextFrom(item.Contents[0])));

        string? GetTextFrom(AnthropicContent content) => content.Text;
    }

    [Fact]
    public async Task ShouldReturnValidChatResponseAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var responses = await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(responses);
        Assert.NotEmpty(responses);
        string content = string.Concat(responses.Select(streamingContent => streamingContent.Content));
        Assert.Equal("Hi! My name is Claude.", content);
        Assert.All(responses, response => Assert.Equal(AuthorRole.Assistant, response.Role));
    }

    [Fact]
    public async Task ShouldReturnValidAnthropicMetadataStartMessageAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var streamingChatMessageContents = await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(streamingChatMessageContents);
        Assert.NotEmpty(streamingChatMessageContents);
        var messageContent = streamingChatMessageContents.First();
        var metadata = messageContent.Metadata as AnthropicMetadata;
        Assert.NotNull(metadata);
        Assert.Null(metadata.FinishReason);
        Assert.Equal("msg_1nZdL29xx5MUA1yADyHTEsnR8uuvGzszyY", metadata.MessageId);
        Assert.Null(metadata.StopSequence);
        Assert.Equal(25, metadata.InputTokenCount);
        Assert.Equal(1, metadata.OutputTokenCount);
    }

    [Fact]
    public async Task ShouldReturnNullAnthropicMetadataDeltaMessagesAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var streamingChatMessageContents = await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(streamingChatMessageContents);
        Assert.NotEmpty(streamingChatMessageContents);
        var deltaMessages = streamingChatMessageContents[1..^1];
        Assert.All(deltaMessages, messageContent => Assert.Null(messageContent.Metadata));
    }

    [Fact]
    public async Task ShouldReturnValidAnthropicMetadataEndMessageAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var streamingChatMessageContents = await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(streamingChatMessageContents);
        Assert.NotEmpty(streamingChatMessageContents);
        var messageContent = streamingChatMessageContents.Last();
        var metadata = messageContent.Metadata as AnthropicMetadata;
        Assert.NotNull(metadata);
        Assert.Equal(AnthropicFinishReason.StopSequence, metadata.FinishReason);
        Assert.Equal("msg_1nZdL29xx5MUA1yADyHTEsnR8uuvGzszyY", metadata.MessageId);
        Assert.Equal("claude", metadata.StopSequence);
        Assert.Equal(0, metadata.InputTokenCount);
        Assert.Equal(15, metadata.OutputTokenCount);
    }

    [Fact]
    public async Task ShouldReturnResponseWithModelIdAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var streamingChatMessageContents = await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(streamingChatMessageContents);
        Assert.NotEmpty(streamingChatMessageContents);
        Assert.All(streamingChatMessageContents, chatMessageContent => Assert.Equal("claude-3-5-sonnet-20240620", chatMessageContent.ModelId));
    }

    [Fact]
    public async Task ShouldUsePromptExecutionSettingsAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new AnthropicPromptExecutionSettings()
        {
            MaxTokens = 102,
            Temperature = 0.45,
            TopP = 0.6f
        };

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory, executionSettings: executionSettings).ToListAsync();

        // Assert
        var request = JsonSerializer.Deserialize<AnthropicRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Equal(executionSettings.MaxTokens, request.MaxTokens);
        Assert.Equal(executionSettings.Temperature, request.Temperature);
        Assert.Equal(executionSettings.TopP, request.TopP);
    }

    [Fact]
    public async Task ShouldThrowInvalidOperationExceptionIfChatHistoryContainsOnlySystemMessageAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = new ChatHistory("System message");

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(
            () => client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync().AsTask());
    }

    [Fact]
    public async Task ShouldThrowInvalidOperationExceptionIfChatHistoryContainsOnlyManySystemMessagesAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = new ChatHistory("System message");
        chatHistory.AddSystemMessage("System message 2");
        chatHistory.AddSystemMessage("System message 3");

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(
            () => client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync().AsTask());
    }

    [Fact]
    public async Task ShouldPassSystemMessageToRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        string[] messages = ["System message", "System message 2"];
        var chatHistory = new ChatHistory(messages[0]);
        chatHistory.AddSystemMessage(messages[1]);
        chatHistory.AddUserMessage("Hello");

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        AnthropicRequest? request = JsonSerializer.Deserialize<AnthropicRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.NotNull(request.SystemPrompt);
        Assert.All(messages, msg => Assert.Contains(msg, request.SystemPrompt, StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public async Task ShouldPassVersionToRequestBodyIfCustomHandlerUsedAsync()
    {
        // Arrange
        var options = new AmazonBedrockAnthropicClientOptions();
        var client = new AnthropicClient("fake-model", new Uri("https://fake-uri.com"),
            bearerTokenProvider: () => ValueTask.FromResult("fake-token"),
            options: options, httpClient: this._httpClient);

        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        AnthropicRequest? request = JsonSerializer.Deserialize<AnthropicRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Equal(options.Version, request.Version);
    }

    [Fact]
    public async Task ShouldThrowArgumentExceptionIfChatHistoryIsEmptyAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = new ChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(
            () => client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync().AsTask());
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-15)]
    public async Task ShouldThrowArgumentExceptionIfExecutionSettingMaxTokensIsLessThanOneAsync(int? maxTokens)
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        AnthropicPromptExecutionSettings executionSettings = new()
        {
            MaxTokens = maxTokens
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(
            () => client.StreamGenerateChatMessageAsync(CreateSampleChatHistory(), executionSettings: executionSettings).ToListAsync().AsTask());
    }

    [Fact]
    public async Task ItCreatesPostRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.Equal(HttpMethod.Post, this._messageHandlerStub.Method);
    }

    [Fact]
    public async Task ItCreatesRequestWithValidUserAgentAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, this._messageHandlerStub.RequestHeaders.UserAgent.ToString());
    }

    [Fact]
    public async Task ItCreatesRequestWithSemanticKernelVersionHeaderAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var expectedVersion = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(AnthropicClient));

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        var header = this._messageHandlerStub.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(expectedVersion, header);
    }

    [Fact]
    public async Task ItCreatesRequestWithValidAnthropicVersionAsync()
    {
        // Arrange
        var options = new AnthropicClientOptions();
        var client = this.CreateChatCompletionClient(options: options);
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.Equal(options.Version, this._messageHandlerStub.RequestHeaders.GetValues("anthropic-version").SingleOrDefault());
    }

    [Fact]
    public async Task ItCreatesRequestWithValidApiKeyAsync()
    {
        // Arrange
        string apiKey = "fake-claude-key";
        var client = this.CreateChatCompletionClient(apiKey: apiKey);
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.Equal(apiKey, this._messageHandlerStub.RequestHeaders.GetValues("x-api-key").SingleOrDefault());
    }

    [Fact]
    public async Task ItCreatesRequestWithJsonContentTypeAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.ContentHeaders);
        Assert.NotNull(this._messageHandlerStub.ContentHeaders.ContentType);
        Assert.Contains("application/json", this._messageHandlerStub.ContentHeaders.ContentType.ToString());
    }

    [Theory]
    [InlineData("custom-header", "custom-value")]
    public async Task ItCreatesRequestWithCustomUriAndCustomHeadersAsync(string headerName, string headerValue)
    {
        // Arrange
        Uri uri = new("https://fake-uri.com");
        using var httpHandler = new CustomHeadersHandler(headerName, headerValue, ChatTestDataFilePath);
        using var httpClient = new HttpClient(httpHandler);
        httpClient.BaseAddress = uri;
        var client = new AnthropicClient("fake-model", "api-key", options: new(), httpClient: httpClient);

        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.Equal(uri, httpHandler.RequestUri);
        Assert.NotNull(httpHandler.RequestHeaders);
        Assert.Equal(headerValue, httpHandler.RequestHeaders.GetValues(headerName).SingleOrDefault());
    }

    private static ChatHistory CreateSampleChatHistory()
    {
        var chatHistory = new ChatHistory("You are a chatbot");
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        return chatHistory;
    }

    private AnthropicClient CreateChatCompletionClient(
        string modelId = "fake-model",
        string? apiKey = null,
        AnthropicClientOptions? options = null,
        HttpClient? httpClient = null)
    {
        return new AnthropicClient(modelId, apiKey ?? "fake-key", options: new(), httpClient: this._httpClient);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
