// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Microsoft.SemanticKernel.Http;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini.Clients;

public sealed class GeminiChatGenerationTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly string _responseContentFinishReasonOther;
    private const string ChatTestDataFilePath = "./TestData/chat_one_response.json";
    private const string ChatTestDataFinishReasonOtherFilePath = "./TestData/chat_finish_reason_other_response.json";

    public GeminiChatGenerationTests()
    {
        this._responseContentFinishReasonOther = File.ReadAllText(ChatTestDataFinishReasonOtherFilePath);
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(ChatTestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldReturnEmptyMessageContentAndNullMetadataIfEmptyJsonInResponseAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent("{}");
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var messages = await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        Assert.Single(messages, item =>
            item.Role == AuthorRole.Assistant &&
            string.IsNullOrEmpty(item.Content) &&
            item.Metadata == null);
    }

    [Fact]
    public async Task ShouldReturnEmptyMessageContentIfNoContentInResponseAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(this._responseContentFinishReasonOther);
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var messages = await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        Assert.Single(messages, item =>
            item.Role == AuthorRole.Assistant && string.IsNullOrEmpty(item.Content) &&
            ((GeminiMetadata)item.Metadata!).FinishReason == GeminiFinishReason.Other);
    }

    [Fact]
    public async Task ShouldContainModelInRequestUriAsync()
    {
        // Arrange
        string modelId = "fake-model234";
        var client = this.CreateChatCompletionClient(modelId: modelId);
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        Assert.Contains(modelId, this._messageHandlerStub.RequestUri.ToString(), StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldContainRolesInRequestAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            await File.ReadAllTextAsync(ChatTestDataFilePath));
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        GeminiRequest? request = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Collection(request.Contents,
            item => Assert.Equal(chatHistory[0].Role, item.Role),
            item => Assert.Equal(chatHistory[1].Role, item.Role),
            item => Assert.Equal(chatHistory[2].Role, item.Role));
    }

    [Fact]
    public async Task ShouldReturnValidChatResponseAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var response = await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        Assert.NotNull(response);
        Assert.Equal("I'm fine, thanks. How are you?", response[0].Content);
        Assert.Equal(AuthorRole.Assistant, response[0].Role);
    }

    [Fact]
    public async Task ShouldReturnValidGeminiMetadataAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var chatMessageContents = await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        GeminiResponse testDataResponse = JsonSerializer.Deserialize<GeminiResponse>(
            await File.ReadAllTextAsync(ChatTestDataFilePath))!;
        var testDataCandidate = testDataResponse.Candidates![0];
        var textContent = chatMessageContents.SingleOrDefault();
        Assert.NotNull(textContent);
        var metadata = textContent.Metadata as GeminiMetadata;
        Assert.NotNull(metadata);
        Assert.Equal(testDataResponse.PromptFeedback!.BlockReason, metadata.PromptFeedbackBlockReason);
        Assert.Equal(testDataCandidate.FinishReason, metadata.FinishReason);
        Assert.Equal(testDataCandidate.Index, metadata.Index);
        Assert.True(metadata.ResponseSafetyRatings!.Count
                    == testDataCandidate.SafetyRatings!.Count);
        Assert.True(metadata.PromptFeedbackSafetyRatings!.Count
                    == testDataResponse.PromptFeedback.SafetyRatings.Count);
        for (var i = 0; i < metadata.ResponseSafetyRatings.Count; i++)
        {
            Assert.Equal(testDataCandidate.SafetyRatings[i].Block, metadata.ResponseSafetyRatings[i].Block);
            Assert.Equal(testDataCandidate.SafetyRatings[i].Category, metadata.ResponseSafetyRatings[i].Category);
            Assert.Equal(testDataCandidate.SafetyRatings[i].Probability, metadata.ResponseSafetyRatings[i].Probability);
        }

        for (var i = 0; i < metadata.PromptFeedbackSafetyRatings.Count; i++)
        {
            Assert.Equal(testDataResponse.PromptFeedback.SafetyRatings[i].Block, metadata.PromptFeedbackSafetyRatings[i].Block);
            Assert.Equal(testDataResponse.PromptFeedback.SafetyRatings[i].Category, metadata.PromptFeedbackSafetyRatings[i].Category);
            Assert.Equal(testDataResponse.PromptFeedback.SafetyRatings[i].Probability, metadata.PromptFeedbackSafetyRatings[i].Probability);
        }

        Assert.Equal(testDataResponse.UsageMetadata!.PromptTokenCount, metadata.PromptTokenCount);
        Assert.Equal(testDataCandidate.TokenCount, metadata.CurrentCandidateTokenCount);
        Assert.Equal(testDataResponse.UsageMetadata.CandidatesTokenCount, metadata.CandidatesTokenCount);
        Assert.Equal(testDataResponse.UsageMetadata.TotalTokenCount, metadata.TotalTokenCount);
    }

    [Fact]
    public async Task ShouldReturnValidDictionaryMetadataAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var chatMessageContents = await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        GeminiResponse testDataResponse = JsonSerializer.Deserialize<GeminiResponse>(
            await File.ReadAllTextAsync(ChatTestDataFilePath))!;
        var testDataCandidate = testDataResponse.Candidates![0];
        var textContent = chatMessageContents.SingleOrDefault();
        Assert.NotNull(textContent);
        var metadata = textContent.Metadata;
        Assert.NotNull(metadata);
        Assert.Equal(testDataResponse.PromptFeedback!.BlockReason, metadata[nameof(GeminiMetadata.PromptFeedbackBlockReason)]);
        Assert.Equal(testDataCandidate.FinishReason, metadata[nameof(GeminiMetadata.FinishReason)]);
        Assert.Equal(testDataCandidate.Index, metadata[nameof(GeminiMetadata.Index)]);
        var responseSafetyRatings = (IList<GeminiSafetyRating>)metadata[nameof(GeminiMetadata.ResponseSafetyRatings)]!;
        for (var i = 0; i < responseSafetyRatings.Count; i++)
        {
            Assert.Equal(testDataCandidate.SafetyRatings![i].Block, responseSafetyRatings[i].Block);
            Assert.Equal(testDataCandidate.SafetyRatings[i].Category, responseSafetyRatings[i].Category);
            Assert.Equal(testDataCandidate.SafetyRatings[i].Probability, responseSafetyRatings[i].Probability);
        }

        var promptSafetyRatings = (IList<GeminiSafetyRating>)metadata[nameof(GeminiMetadata.PromptFeedbackSafetyRatings)]!;
        for (var i = 0; i < promptSafetyRatings.Count; i++)
        {
            Assert.Equal(testDataResponse.PromptFeedback.SafetyRatings[i].Block, promptSafetyRatings[i].Block);
            Assert.Equal(testDataResponse.PromptFeedback.SafetyRatings[i].Category, promptSafetyRatings[i].Category);
            Assert.Equal(testDataResponse.PromptFeedback.SafetyRatings[i].Probability, promptSafetyRatings[i].Probability);
        }

        Assert.Equal(testDataResponse.UsageMetadata!.PromptTokenCount, metadata[nameof(GeminiMetadata.PromptTokenCount)]);
        Assert.Equal(testDataCandidate.TokenCount, metadata[nameof(GeminiMetadata.CurrentCandidateTokenCount)]);
        Assert.Equal(testDataResponse.UsageMetadata.CandidatesTokenCount, metadata[nameof(GeminiMetadata.CandidatesTokenCount)]);
        Assert.Equal(testDataResponse.UsageMetadata.TotalTokenCount, metadata[nameof(GeminiMetadata.TotalTokenCount)]);
    }

    [Fact]
    public async Task ShouldReturnResponseWithModelIdAsync()
    {
        // Arrange
        string modelId = "fake-model";
        var client = this.CreateChatCompletionClient(modelId: modelId);
        var chatHistory = CreateSampleChatHistory();

        // Act
        var chatMessageContents = await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        var chatMessageContent = chatMessageContents.SingleOrDefault();
        Assert.NotNull(chatMessageContent);
        Assert.Equal(modelId, chatMessageContent.ModelId);
    }

    [Fact]
    public async Task ShouldUsePromptExecutionSettingsAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 102,
            Temperature = 0.45,
            TopP = 0.6,
            AudioTimestamp = true,
            ResponseMimeType = "application/json"
        };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, executionSettings: executionSettings);

        // Assert
        var geminiRequest = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(geminiRequest);
        Assert.Equal(executionSettings.MaxTokens, geminiRequest.Configuration!.MaxOutputTokens);
        Assert.Equal(executionSettings.Temperature, geminiRequest.Configuration!.Temperature);
        Assert.Equal(executionSettings.AudioTimestamp, geminiRequest.Configuration!.AudioTimestamp);
        Assert.Equal(executionSettings.ResponseMimeType, geminiRequest.Configuration!.ResponseMimeType);
        Assert.Equal(executionSettings.TopP, geminiRequest.Configuration!.TopP);
    }

    [Fact]
    public async Task ShouldThrowInvalidOperationExceptionIfChatHistoryContainsOnlySystemMessageAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = new ChatHistory("System message");

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(
            () => client.GenerateChatMessageAsync(chatHistory));
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
            () => client.GenerateChatMessageAsync(chatHistory));
    }

    [Fact]
    public async Task ShouldPassSystemMessageToRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        string message = "System message";
        var chatHistory = new ChatHistory(message);
        chatHistory.AddUserMessage("Hello");

        // Act
        await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        GeminiRequest? request = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.NotNull(request.SystemInstruction);
        var systemMessage = request.SystemInstruction.Parts![0].Text;
        Assert.Null(request.SystemInstruction.Role);
        Assert.Equal(message, systemMessage);
    }

    [Fact]
    public async Task ShouldPassMultipleSystemMessagesToRequestAsync()
    {
        // Arrange
        string[] messages = ["System message 1", "System message 2", "System message 3"];
        var client = this.CreateChatCompletionClient();
        var chatHistory = new ChatHistory(messages[0]);
        chatHistory.AddSystemMessage(messages[1]);
        chatHistory.AddSystemMessage(messages[2]);
        chatHistory.AddUserMessage("Hello");

        // Act
        await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        GeminiRequest? request = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.NotNull(request.SystemInstruction);
        Assert.Null(request.SystemInstruction.Role);
        Assert.Collection(request.SystemInstruction.Parts!,
            item => Assert.Equal(messages[0], item.Text),
            item => Assert.Equal(messages[1], item.Text),
            item => Assert.Equal(messages[2], item.Text));
    }

    [Fact]
    public async Task ShouldThrowArgumentExceptionIfChatHistoryIsEmptyAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = new ChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(
            () => client.GenerateChatMessageAsync(chatHistory));
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-15)]
    public async Task ShouldThrowArgumentExceptionIfExecutionSettingMaxTokensIsLessThanOneAsync(int? maxTokens)
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        GeminiPromptExecutionSettings executionSettings = new()
        {
            MaxTokens = maxTokens
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(
            () => client.GenerateChatMessageAsync(CreateSampleChatHistory(), executionSettings: executionSettings));
    }

    [Fact]
    public async Task ItCreatesPostRequestIfBearerIsSpecifiedWithAuthorizationHeaderAsync()
    {
        // Arrange
        string bearerKey = "fake-key";
        var client = this.CreateChatCompletionClient(bearerKey: bearerKey);
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.NotNull(this._messageHandlerStub.RequestHeaders.Authorization);
        Assert.Equal($"Bearer {bearerKey}", this._messageHandlerStub.RequestHeaders.Authorization.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        Assert.Equal(HttpMethod.Post, this._messageHandlerStub.Method);
    }

    [Fact]
    public async Task ItCreatesPostRequestWithValidUserAgentAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, this._messageHandlerStub.RequestHeaders.UserAgent.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestWithSemanticKernelVersionHeaderAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var expectedVersion = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientBase));

        // Act
        await client.GenerateChatMessageAsync(chatHistory);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        var header = this._messageHandlerStub.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(expectedVersion, header);
    }

    [Fact]
    public async Task ItCreatesPostRequestWithResponseSchemaPropertyAsync()
    {
        // Get a mock logger that will return true for IsEnabled(LogLevel.Trace)
        var mockLogger = new Mock<ILogger<GeminiChatGenerationTests>>();
        mockLogger.Setup(x => x.IsEnabled(LogLevel.Trace)).Returns(true);

        // Arrange
        var client = this.CreateChatCompletionClient(logger: mockLogger.Object);
        var chatHistory = CreateSampleChatHistory();
        var settings = new GeminiPromptExecutionSettings { ResponseMimeType = "application/json", ResponseSchema = typeof(List<int>) };

        // Act
        await client.GenerateChatMessageAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);

        var responseBody = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);

        Assert.Contains("responseSchema", responseBody, StringComparison.Ordinal);
        Assert.Contains("\"responseSchema\":{\"type\":\"array\",\"items\":{\"type\":\"integer\"}}", responseBody, StringComparison.Ordinal);
        Assert.Contains("\"responseMimeType\":\"application/json\"", responseBody, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ItCanUseValueTasksSequentiallyForBearerTokenAsync()
    {
        // Arrange
        var bearerTokenGenerator = new BearerTokenGenerator()
        {
            BearerKeys = ["key1", "key2", "key3"]
        };

        var responseContent = File.ReadAllText(ChatTestDataFilePath);
        using var content1 = new HttpResponseMessage { Content = new StringContent(responseContent) };
        using var content2 = new HttpResponseMessage { Content = new StringContent(responseContent) };

        using MultipleHttpMessageHandlerStub multipleMessageHandlerStub = new()
        {
            ResponsesToReturn = [content1, content2]
        };
        using var httpClient = new HttpClient(multipleMessageHandlerStub, false);

        var client = new GeminiChatCompletionClient(
            httpClient: httpClient,
            modelId: "fake-model",
            apiVersion: VertexAIVersion.V1,
            bearerTokenProvider: bearerTokenGenerator.GetBearerToken,
            location: "fake-location",
            projectId: "fake-project-id");

        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.GenerateChatMessageAsync(chatHistory);
        await client.GenerateChatMessageAsync(chatHistory);
        var firstRequestHeader = multipleMessageHandlerStub.RequestHeaders[0]?.GetValues("Authorization").SingleOrDefault();
        var secondRequestHeader = multipleMessageHandlerStub.RequestHeaders[1]?.GetValues("Authorization").SingleOrDefault();

        // Assert
        Assert.NotNull(firstRequestHeader);
        Assert.NotNull(secondRequestHeader);
        Assert.NotEqual(firstRequestHeader, secondRequestHeader);
        Assert.Equal("Bearer key1", firstRequestHeader);
        Assert.Equal("Bearer key2", secondRequestHeader);
    }

    [Theory]
    [InlineData("https://malicious-site.com")]
    [InlineData("http://internal-network.local")]
    [InlineData("ftp://attacker.com")]
    [InlineData("//bypass.com")]
    [InlineData("javascript:alert(1)")]
    [InlineData("data:text/html,<script>alert(1)</script>")]
    public void ItThrowsOnLocationUrlInjectionAttempt(string maliciousLocation)
    {
        // Arrange
        var bearerTokenGenerator = new BearerTokenGenerator()
        {
            BearerKeys = ["key1", "key2", "key3"]
        };

        using var httpClient = new HttpClient();

        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
        {
            var client = new GeminiChatCompletionClient(
                httpClient: httpClient,
                modelId: "fake-model",
                apiVersion: VertexAIVersion.V1,
                bearerTokenProvider: bearerTokenGenerator.GetBearerToken,
                location: maliciousLocation,
                projectId: "fake-project-id");
        });
    }

    [Theory]
    [InlineData("useast1")]
    [InlineData("us-east1")]
    [InlineData("europe-west4")]
    [InlineData("asia-northeast1")]
    [InlineData("us-central1-a")]
    [InlineData("northamerica-northeast1")]
    [InlineData("australia-southeast1")]
    public void ItAcceptsValidHostnameSegments(string validLocation)
    {
        // Arrange
        var bearerTokenGenerator = new BearerTokenGenerator()
        {
            BearerKeys = ["key1", "key2", "key3"]
        };

        using var httpClient = new HttpClient();

        // Act & Assert
        var exception = Record.Exception(() =>
        {
            var client = new GeminiChatCompletionClient(
                httpClient: httpClient,
                modelId: "fake-model",
                apiVersion: VertexAIVersion.V1,
                bearerTokenProvider: bearerTokenGenerator.GetBearerToken,
                location: validLocation,
                projectId: "fake-project-id");
        });

        Assert.Null(exception);
    }

    private sealed class BearerTokenGenerator()
    {
        private int _index = 0;
        public required List<string> BearerKeys { get; init; }

        public ValueTask<string> GetBearerToken() => ValueTask.FromResult(this.BearerKeys[this._index++]);
    }

    private static ChatHistory CreateSampleChatHistory()
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        return chatHistory;
    }

    private GeminiChatCompletionClient CreateChatCompletionClient(
        string modelId = "fake-model",
        string? bearerKey = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        if (bearerKey is not null)
        {
            return new GeminiChatCompletionClient(
                httpClient: httpClient ?? this._httpClient,
                modelId: modelId,
                apiVersion: VertexAIVersion.V1,
                bearerTokenProvider: () => new ValueTask<string>(bearerKey),
                location: "fake-location",
                projectId: "fake-project-id",
                logger: logger);
        }

        return new GeminiChatCompletionClient(
            httpClient: httpClient ?? this._httpClient,
            modelId: modelId,
            apiVersion: GoogleAIVersion.V1,
            apiKey: "fake-key",
            logger: logger);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
