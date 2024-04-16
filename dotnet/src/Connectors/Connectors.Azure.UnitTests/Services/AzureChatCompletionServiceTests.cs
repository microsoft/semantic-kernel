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
using Microsoft.SemanticKernel.Connectors.Azure;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Azure.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureChatCompletionService"/>
/// </summary>
public sealed class AzureChatCompletionServiceTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AzureChatCompletionServiceTests()
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
            new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id");

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
            new AzureChatCompletionService("deployment", new Uri("https://endpoint"), credentials, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureChatCompletionService("deployment", new Uri("https://endpoint"), credentials, "model-id");

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
            new AzureChatCompletionService("deployment", client, "model-id", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureChatCompletionService("deployment", client, "model-id");

        // Assert
        Assert.NotNull(service);
        Assert.Equal("model-id", service.Attributes["ModelId"]);
    }

    [Fact]
    public async Task GetChatMessageContentsWithEmptyChoicesThrowsExceptionAsync()
    {
        // Arrange
        var service = new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id", this._httpClient);
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
        var service = new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id", this._httpClient);
        var settings = new AzurePromptExecutionSettings { ResultsPerPrompt = resultsPerPrompt };

        // Act & Assert
        var exception = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => service.GetChatMessageContentsAsync([], settings));

        Assert.Contains("The value must be in range between", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task GetChatMessageContentsHandlesSettingsCorrectlyAsync()
    {
        // Arrange
        var service = new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id", this._httpClient);
        var settings = new AzurePromptExecutionSettings()
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
        chatHistory.AddUserMessage(new ChatMessageContentItemCollection { new ImageContent(new Uri("https://image")), new TextContent("User Message") });
        chatHistory.AddSystemMessage("System Message");
        chatHistory.AddAssistantMessage("Assistant Message");

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(TestHelper.GetTestResponse("chat_completion_test_response.json"))
        });

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        var requestContent = this._messageHandlerStub.RequestContents[0];

        Assert.NotNull(requestContent);

        var content = JsonSerializer.Deserialize<JsonElement>(Encoding.UTF8.GetString(requestContent));

        var messages = content.GetProperty("messages");

        var userMessage = messages[0];
        var userMessageCollection = messages[1];
        var systemMessage = messages[2];
        var assistantMessage = messages[3];

        Assert.Equal("user", userMessage.GetProperty("role").GetString());
        Assert.Equal("User Message", userMessage.GetProperty("content").GetString());

        Assert.Equal("user", userMessageCollection.GetProperty("role").GetString());
        var contentItems = userMessageCollection.GetProperty("content");
        Assert.Equal(2, contentItems.GetArrayLength());
        Assert.Equal("https://image/", contentItems[0].GetProperty("image_url").GetProperty("url").GetString());
        Assert.Equal("image_url", contentItems[0].GetProperty("type").GetString());
        Assert.Equal("User Message", contentItems[1].GetProperty("text").GetString());
        Assert.Equal("text", contentItems[1].GetProperty("type").GetString());

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
        var service = new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id", this._httpClient);
        var settings = new AzurePromptExecutionSettings()
        {
            ResponseFormat = responseFormat
        };

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(TestHelper.GetTestResponse("chat_completion_test_response.json"))
        });

        // Act
        var result = await service.GetChatMessageContentsAsync([], settings);

        // Assert
        var requestContent = this._messageHandlerStub.RequestContents[0];

        Assert.NotNull(requestContent);

        var content = JsonSerializer.Deserialize<JsonElement>(Encoding.UTF8.GetString(requestContent));

        Assert.Equal(expectedResponseType, content.GetProperty("response_format").GetProperty("type").GetString());
    }

    [Fact]
    public async Task GetChatMessageContentsWorksCorrectlyAsync()
    {
        // Arrange
        var kernel = Kernel.CreateBuilder().Build();
        var service = new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id", this._httpClient);

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(TestHelper.GetTestResponse("chat_completion_test_response.json"))
        });

        // Act
        var result = await service.GetChatMessageContentsAsync([], null, kernel);

        // Assert
        Assert.True(result.Count > 0);
        Assert.Equal("Test chat response", result[0].Content);

        var usage = result[0].Metadata?["Usage"] as CompletionsUsage;

        Assert.NotNull(usage);
        Assert.Equal(55, usage.PromptTokens);
        Assert.Equal(100, usage.CompletionTokens);
        Assert.Equal(155, usage.TotalTokens);

        Assert.Equal("stop", result[0].Metadata?["FinishReason"]);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id", this._httpClient);
        using var stream = new MemoryStream(Encoding.UTF8.GetBytes(TestHelper.GetTestResponse("chat_completion_streaming_test_response.txt")));

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        });

        // Act & Assert
        var enumerator = service.GetStreamingChatMessageContentsAsync([]).GetAsyncEnumerator();

        await enumerator.MoveNextAsync();
        Assert.Equal("Test chat streaming response", enumerator.Current.Content);

        await enumerator.MoveNextAsync();
        Assert.Equal("stop", enumerator.Current.Metadata?["FinishReason"]);
    }

    [Fact]
    public async Task GetChatMessageContentsUsesPromptAndSettingsCorrectlyAsync()
    {
        // Arrange
        const string Prompt = "This is test prompt";
        const string SystemMessage = "This is test system message";

        var service = new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id", this._httpClient);
        var settings = new AzurePromptExecutionSettings() { ChatSystemPrompt = SystemMessage };

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(TestHelper.GetTestResponse("chat_completion_test_response.json"))
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

        Assert.Equal(SystemMessage, messages[0].GetProperty("content").GetString());
        Assert.Equal("system", messages[0].GetProperty("role").GetString());

        Assert.Equal(Prompt, messages[1].GetProperty("content").GetString());
        Assert.Equal("user", messages[1].GetProperty("role").GetString());
    }

    [Fact]
    public async Task GetChatMessageContentsWithChatMessageContentItemCollectionAndSettingsCorrectlyAsync()
    {
        // Arrange
        const string Prompt = "This is test prompt";
        const string SystemMessage = "This is test system message";
        const string AssistantMessage = "This is assistant message";
        const string CollectionItemPrompt = "This is collection item prompt";

        var service = new AzureChatCompletionService("deployment", new Uri("https://endpoint"), "api-key", "model-id", this._httpClient);
        var settings = new AzurePromptExecutionSettings() { ChatSystemPrompt = SystemMessage };

        this._messageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(TestHelper.GetTestResponse("chat_completion_test_response.json"))
        });

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(Prompt);
        chatHistory.AddAssistantMessage(AssistantMessage);
        chatHistory.AddUserMessage(new ChatMessageContentItemCollection()
        {
            new TextContent(CollectionItemPrompt),
            new ImageContent(new Uri("https://image"))
        });

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.True(result.Count > 0);
        Assert.Equal("Test chat response", result[0].Content);

        var requestContentByteArray = this._messageHandlerStub.RequestContents[0];

        Assert.NotNull(requestContentByteArray);

        var requestContent = JsonSerializer.Deserialize<JsonElement>(Encoding.UTF8.GetString(requestContentByteArray));

        var messages = requestContent.GetProperty("messages");

        Assert.Equal(4, messages.GetArrayLength());

        Assert.Equal(SystemMessage, messages[0].GetProperty("content").GetString());
        Assert.Equal("system", messages[0].GetProperty("role").GetString());

        Assert.Equal(Prompt, messages[1].GetProperty("content").GetString());
        Assert.Equal("user", messages[1].GetProperty("role").GetString());

        Assert.Equal(AssistantMessage, messages[2].GetProperty("content").GetString());
        Assert.Equal("assistant", messages[2].GetProperty("role").GetString());

        var contentItems = messages[3].GetProperty("content");
        Assert.Equal(2, contentItems.GetArrayLength());
        Assert.Equal(CollectionItemPrompt, contentItems[0].GetProperty("text").GetString());
        Assert.Equal("text", contentItems[0].GetProperty("type").GetString());
        Assert.Equal("https://image/", contentItems[1].GetProperty("image_url").GetProperty("url").GetString());
        Assert.Equal("image_url", contentItems[1].GetProperty("type").GetString());
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    public static TheoryData<object, string?> ResponseFormats => new()
    {
        { new FakeChatCompletionsResponseFormat(), null },
        { "json_object", "json_object" },
        { "text", "text" }
    };

    private sealed class FakeChatCompletionsResponseFormat : ChatCompletionsResponseFormat { }
}
