// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini.Clients;

public sealed class GeminiChatStreamingTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly string _responseContentFinishReasonOther;
    private const string StreamTestDataFilePath = "./TestData/chat_stream_response.json";
    private const string StreamTestDataFinishReasonOtherFilePath = "./TestData/chat_stream_finish_reason_other_response.json";

    public GeminiChatStreamingTests()
    {
        this._responseContentFinishReasonOther = File.ReadAllText(StreamTestDataFinishReasonOtherFilePath);
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(StreamTestDataFilePath));

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
        var messages = await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

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
        var messages = await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

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
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        Assert.Contains(modelId, this._messageHandlerStub.RequestUri.ToString(), StringComparison.Ordinal);
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
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("Explain me world in many word ;)");

        // Act
        var chatMessageContents = await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        List<GeminiResponse> testDataResponse = JsonSerializer.Deserialize<List<GeminiResponse>>(
            await File.ReadAllTextAsync(StreamTestDataFilePath))!;

        Assert.NotEmpty(chatMessageContents);
        Assert.Equal(testDataResponse.Count, chatMessageContents.Count);
        for (int i = 0; i < testDataResponse.Count; i++)
        {
            Assert.Equal(
                testDataResponse[i].Candidates![0].Content!.Parts![0].Text,
                chatMessageContents[i].Content);
            Assert.Equal(
                testDataResponse[i].Candidates![0].Content!.Role,
                chatMessageContents[i].Role);
        }
    }

    [Fact]
    public async Task ShouldReturnValidGeminiMetadataAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var chatMessageContents =
            await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        GeminiResponse testDataResponse = JsonSerializer.Deserialize<List<GeminiResponse>>(
            await File.ReadAllTextAsync(StreamTestDataFilePath))![0];
        var testDataCandidate = testDataResponse.Candidates![0];
        var textContent = chatMessageContents.FirstOrDefault();
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
        Assert.Equal(testDataResponse.UsageMetadata!.CachedContentTokenCount, metadata.CachedContentTokenCount);
        Assert.Equal(testDataResponse.UsageMetadata!.ThoughtsTokenCount, metadata.ThoughtsTokenCount);
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
        var chatMessageContents =
            await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        GeminiResponse testDataResponse = JsonSerializer.Deserialize<List<GeminiResponse>>(
            await File.ReadAllTextAsync(StreamTestDataFilePath))![0];
        var testDataCandidate = testDataResponse.Candidates![0];
        var textContent = chatMessageContents.FirstOrDefault();
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
        Assert.Equal(testDataResponse.UsageMetadata!.CachedContentTokenCount, metadata[nameof(GeminiMetadata.CachedContentTokenCount)]);
        Assert.Equal(testDataResponse.UsageMetadata!.ThoughtsTokenCount, metadata[nameof(GeminiMetadata.ThoughtsTokenCount)]);
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
        var chatMessageContents =
            await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        var chatMessageContent = chatMessageContents.FirstOrDefault();
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
            TopP = 0.6
        };

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory, executionSettings: executionSettings).ToListAsync();

        // Assert
        var geminiRequest = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(geminiRequest);
        Assert.Equal(executionSettings.MaxTokens, geminiRequest.Configuration!.MaxOutputTokens);
        Assert.Equal(executionSettings.Temperature, geminiRequest.Configuration!.Temperature);
        Assert.Equal(executionSettings.TopP, geminiRequest.Configuration!.TopP);
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
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

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
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

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
            async () => await client.StreamGenerateChatMessageAsync(CreateSampleChatHistory(), executionSettings: executionSettings).ToListAsync());
    }

    [Fact]
    public async Task ItCreatesPostRequestIfBearerIsSpecifiedWithAuthorizationHeaderAsync()
    {
        // Arrange
        string bearerKey = "fake-key";
        var client = this.CreateChatCompletionClient(bearerKey: bearerKey);
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

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
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

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
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

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
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        var header = this._messageHandlerStub.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(expectedVersion, header);
    }

    [Fact]
    public async Task ItCreatesPostRequestWithApiKeyInHeaderAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        var apiKeyHeader = this._messageHandlerStub.RequestHeaders.GetValues("x-goog-api-key").SingleOrDefault();
        Assert.NotNull(apiKeyHeader);
        Assert.Equal("fake-key", apiKeyHeader);
    }

    [Fact]
    public async Task ItCreatesPostRequestWithoutApiKeyInUrlAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestUri);
        Assert.DoesNotContain("key=", this._messageHandlerStub.RequestUri.ToString());
    }

    [Fact]
    public async Task ShouldHandleStreamingThoughtPartsAsync()
    {
        // Arrange
        var streamingResponse = """
            data: {"candidates": [{"content": {"parts": [{"text": "Let me think...", "thought": true}], "role": "model"}, "index": 0}]}

            data: {"candidates": [{"content": {"parts": [{"text": "The answer is"}], "role": "model"}, "index": 0}]}

            data: {"candidates": [{"content": {"parts": [{"text": " 42."}], "role": "model"}, "finishReason": "STOP", "index": 0}]}

            """;

        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(streamingResponse);
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var messages = await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        Assert.Equal(3, messages.Count);

        // First message should contain thought
        var firstMessage = messages[0];
        Assert.True(string.IsNullOrEmpty(firstMessage.Content));
        Assert.Single(firstMessage.Items);
#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        var thoughtItem = firstMessage.Items.OfType<StreamingReasoningContent>().Single();
#pragma warning restore SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        Assert.Equal("Let me think...", thoughtItem.InnerContent);

        // Second and third messages contain regular text
        var secondMessage = messages[1];
        Assert.Equal("The answer is", secondMessage.Content);

        var thirdMessage = messages[2];
        Assert.Equal(" 42.", thirdMessage.Content);
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
        HttpClient? httpClient = null)
    {
        if (bearerKey is not null)
        {
            return new GeminiChatCompletionClient(
                httpClient: httpClient ?? this._httpClient,
                modelId: modelId,
                bearerTokenProvider: () => new ValueTask<string>(bearerKey),
                apiVersion: VertexAIVersion.V1,
                location: "fake-location",
                projectId: "fake-project-id");
        }

        return new GeminiChatCompletionClient(
            httpClient: httpClient ?? this._httpClient,
            modelId: modelId,
            apiVersion: GoogleAIVersion.V1,
            apiKey: "fake-key");
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
