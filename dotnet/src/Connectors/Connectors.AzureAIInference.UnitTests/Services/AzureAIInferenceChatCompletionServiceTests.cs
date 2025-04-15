// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Azure;
using Azure.AI.Inference;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureAIInference;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureAIInference.UnitTests.Services;

/// <summary>
/// Tests for the <see cref="AzureAIInferenceChatCompletionService"/> class.
/// </summary>
[Obsolete("Keeping this test until the service is removed from code-base")]
public sealed class AzureAIInferenceChatCompletionServiceTests : IDisposable
{
    private readonly Uri _endpoint = new("https://localhost:1234");
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly MultipleHttpMessageHandlerStub _multiMessageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly HttpClient _httpClientWithBaseAddress;
    private readonly AzureAIInferencePromptExecutionSettings _executionSettings;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;
    private readonly ChatHistory _chatHistoryForTest = [new ChatMessageContent(AuthorRole.User, "test")];

    public AzureAIInferenceChatCompletionServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._multiMessageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._httpClientWithBaseAddress = new HttpClient(this._messageHandlerStub, false) { BaseAddress = this._endpoint };
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
        this._executionSettings = new AzureAIInferencePromptExecutionSettings();
    }

    /// <summary>
    /// Checks that the constructors work as expected.
    /// </summary>
    [Fact]
    public void ConstructorsWorksAsExpected()
    {
        // Arrange
        using var httpClient = new HttpClient() { BaseAddress = this._endpoint };
        ChatCompletionsClient client = new(this._endpoint, new AzureKeyCredential("api-key"));

        // Act & Assert
        // Endpoint constructor
        new AzureAIInferenceChatCompletionService(modelId: "model", endpoint: this._endpoint, apiKey: null); // Only the endpoint
        new AzureAIInferenceChatCompletionService(modelId: "model", httpClient: httpClient, apiKey: null); // Only the HttpClient with a BaseClass defined
        new AzureAIInferenceChatCompletionService(modelId: "model", endpoint: this._endpoint, apiKey: null); // ModelId and endpoint
        new AzureAIInferenceChatCompletionService(modelId: "model", apiKey: "api-key", endpoint: this._endpoint); // ModelId, apiKey, and endpoint
        new AzureAIInferenceChatCompletionService(modelId: "model", endpoint: this._endpoint, apiKey: null, loggerFactory: NullLoggerFactory.Instance); // Endpoint and loggerFactory

        // Breaking Glass constructor
        new AzureAIInferenceChatCompletionService(modelId: null, chatClient: client); // Client without model 
        new AzureAIInferenceChatCompletionService(modelId: "model", chatClient: client); // Client
        new AzureAIInferenceChatCompletionService(modelId: "model", chatClient: client, loggerFactory: NullLoggerFactory.Instance); // Client
    }

    [Theory]
    [InlineData("http://localhost:1234/chat/completions")] // Uses full path when provided
    [InlineData("http://localhost:1234/v2/chat/completions")] // Uses full path when provided
    [InlineData("http://localhost:1234")]
    [InlineData("http://localhost:8080")]
    [InlineData("https://something:8080")] // Accepts TLS Secured endpoints
    [InlineData("http://localhost:1234/v2")]
    [InlineData("http://localhost:8080/v2")]
    public async Task ItUsesCustomEndpointsWhenProvidedDirectlyAsync(string endpoint)
    {
        // Arrange
        var chatCompletion = new AzureAIInferenceChatCompletionService(modelId: "any", apiKey: null, httpClient: this._httpClient, endpoint: new Uri(endpoint));
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = this.CreateDefaultStringContent() };

        // Act
        await chatCompletion.GetChatMessageContentsAsync(this._chatHistoryForTest, this._executionSettings);

        // Assert
        Assert.StartsWith($"{endpoint}/chat/completions", this._messageHandlerStub.RequestUri!.ToString());
    }

    [Theory]
    [InlineData("http://localhost:1234/chat/completions")] // Uses full path when provided
    [InlineData("http://localhost:1234/v2/chat/completions")] // Uses full path when provided
    [InlineData("http://localhost:1234")]
    [InlineData("http://localhost:8080")]
    [InlineData("https://something:8080")] // Accepts TLS Secured endpoints
    [InlineData("http://localhost:1234/v2")]
    [InlineData("http://localhost:8080/v2")]
    public async Task ItPrioritizesCustomEndpointOverHttpClientBaseAddressAsync(string endpoint)
    {
        // Arrange
        this._httpClient.BaseAddress = new Uri("http://should-be-overridden");
        var chatCompletion = new AzureAIInferenceChatCompletionService(modelId: "any", apiKey: null, httpClient: this._httpClient, endpoint: new Uri(endpoint));
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = this.CreateDefaultStringContent() };

        // Act
        await chatCompletion.GetChatMessageContentsAsync(this._chatHistoryForTest, this._executionSettings);

        // Assert
        Assert.StartsWith($"{endpoint}/chat/completions", this._messageHandlerStub.RequestUri!.ToString());
    }

    [Fact]
    public async Task ItUsesHttpClientBaseAddressWhenNoEndpointIsProvidedAsync()
    {
        // Arrange
        this._httpClient.BaseAddress = this._endpoint;
        var chatCompletion = new AzureAIInferenceChatCompletionService(modelId: "any", httpClient: this._httpClient);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        { Content = this.CreateDefaultStringContent() };

        // Act
        await chatCompletion.GetChatMessageContentsAsync(this._chatHistoryForTest, this._executionSettings);

        // Assert
        Assert.StartsWith(this._endpoint.ToString(), this._messageHandlerStub.RequestUri?.ToString());
    }

    [Fact]
    public void ItThrowsIfNoEndpointOrNoHttpClientBaseAddressIsProvided()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AzureAIInferenceChatCompletionService(modelId: "model", endpoint: null, httpClient: this._httpClient));
    }

    [Fact]
    public async Task ItGetChatMessageContentsShouldHaveModelIdDefinedAsync()
    {
        // Arrange
        var chatCompletion = new AzureAIInferenceChatCompletionService(modelId: "model", apiKey: "NOKEY", httpClient: this._httpClientWithBaseAddress);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = this.CreateDefaultStringContent() };

        var chatHistory = new ChatHistory();
        chatHistory.AddMessage(AuthorRole.User, "Hello");

        // Act
        var chatMessage = await chatCompletion.GetChatMessageContentAsync(chatHistory, this._executionSettings);

        // Assert
        Assert.NotNull(chatMessage.ModelId);
        Assert.Equal("phi3-medium-4k", chatMessage.ModelId);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureAIInferenceChatCompletionService(modelId: "model", httpClient: this._httpClientWithBaseAddress);
        await using var stream = File.OpenRead("TestData/chat_completion_streaming_response.txt");

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        // Act & Assert
        var enumerator = service.GetStreamingChatMessageContentsAsync([]).GetAsyncEnumerator();

        await enumerator.MoveNextAsync();
        Assert.Equal(AuthorRole.Assistant, enumerator.Current.Role);

        await enumerator.MoveNextAsync();
        Assert.Equal("Test content", enumerator.Current.Content);
        Assert.IsType<StreamingChatCompletionsUpdate>(enumerator.Current.InnerContent);
        StreamingChatCompletionsUpdate innerContent = (StreamingChatCompletionsUpdate)enumerator.Current.InnerContent;
        Assert.Equal("stop", innerContent.FinishReason);
    }

    [Fact]
    public async Task GetChatMessageContentsWithChatMessageContentItemCollectionCorrectlyAsync()
    {
        // Arrange
        const string Prompt = "This is test prompt";
        const string AssistantMessage = "This is assistant message";
        const string CollectionItemPrompt = "This is collection item prompt";
        var chatCompletion = new AzureAIInferenceChatCompletionService(modelId: "gpt-3.5-turbo", apiKey: "NOKEY", httpClient: this._httpClientWithBaseAddress);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        { Content = this.CreateDefaultStringContent() };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(Prompt);
        chatHistory.AddAssistantMessage(AssistantMessage);
        chatHistory.AddUserMessage(
        [
            new TextContent(CollectionItemPrompt),
            new ImageContent(new Uri("https://image"))
        ]);

        // Act
        await chatCompletion.GetChatMessageContentsAsync(chatHistory);

        // Assert
        var actualRequestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(actualRequestContent);
        var optionsJson = JsonSerializer.Deserialize<JsonElement>(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");

        Assert.Equal(3, messages.GetArrayLength());

        Assert.Contains(Prompt, messages[0].GetProperty("content").GetRawText());
        Assert.Equal("user", messages[0].GetProperty("role").GetString());

        Assert.Equal(AssistantMessage, messages[1].GetProperty("content").GetString());
        Assert.Equal("assistant", messages[1].GetProperty("role").GetString());

        var contentItems = messages[2].GetProperty("content");
        Assert.Equal(2, contentItems.GetArrayLength());
        Assert.Equal(CollectionItemPrompt, contentItems[0].GetProperty("text").GetString());
        Assert.Equal("text", contentItems[0].GetProperty("type").GetString());
        Assert.Equal("https://image/", contentItems[1].GetProperty("image_url").GetProperty("url").GetString());
        Assert.Equal("image_url", contentItems[1].GetProperty("type").GetString());
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
        // Arrange
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
                format = formatValue == "text" ? new ChatCompletionsResponseFormatText() : new ChatCompletionsResponseFormatJsonObject();
                break;
        }

        var sut = new AzureAIInferenceChatCompletionService("any", httpClient: this._httpClientWithBaseAddress);
        AzureAIInferencePromptExecutionSettings executionSettings = new() { ResponseFormat = format };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_response.json"))
        };

        // Act
        var result = await sut.GetChatMessageContentAsync(this._chatHistoryForTest, executionSettings);

        // Assert
        Assert.NotNull(result);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._httpClientWithBaseAddress.Dispose();
        this._messageHandlerStub.Dispose();
        this._multiMessageHandlerStub.Dispose();
    }

    private StringContent CreateDefaultStringContent()
    {
        return new StringContent(File.ReadAllText("TestData/chat_completion_response.json"));
    }
}
