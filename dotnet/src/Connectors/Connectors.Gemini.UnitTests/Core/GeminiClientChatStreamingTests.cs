#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Gemini.Core;
using Microsoft.SemanticKernel.Connectors.Gemini.Settings;
using SemanticKernel.UnitTests;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests.Core;

public sealed class GeminiClientChatStreamingTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string StreamTestDataFilePath = "./TestData/chat_stream_response.json";

    public GeminiClientChatStreamingTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(StreamTestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldContainRolesInRequestAsync()
    {
        // Arrange
        var client = new GeminiClient("fake-model", "fake-api-key", this._httpClient);
        var chatHistory = CreateChatHistory();

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        GeminiRequest? request = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Collection(request.Contents,
            item => Assert.Equal(GeminiChatRole.FromAuthorRole(chatHistory[0].Role), item.Role),
            item => Assert.Equal(GeminiChatRole.FromAuthorRole(chatHistory[1].Role), item.Role),
            item => Assert.Equal(GeminiChatRole.FromAuthorRole(chatHistory[2].Role), item.Role));
    }

    [Fact]
    public async Task ShouldReturnValidChatResponseAsync()
    {
        // Arrange
        var client = new GeminiClient("fake-model", "fake-api-key", this._httpClient);
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
                testDataResponse[i].Candidates[0].Content.Parts[0].Text,
                chatMessageContents[i].Content);
            Assert.Equal(
                testDataResponse[i].Candidates[0].Content.Role,
                GeminiChatRole.FromAuthorRole((AuthorRole)chatMessageContents[i].Role!));
        }
    }

    [Fact]
    public async Task ShouldReturnValidMetadataAsync()
    {
        // Arrange
        var client = new GeminiClient("fake-model", "fake-api-key", this._httpClient);
        var chatHistory = CreateChatHistory();

        // Act
        var chatMessageContents =
            await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        GeminiResponse testDataResponse = JsonSerializer.Deserialize<List<GeminiResponse>>(
            await File.ReadAllTextAsync(StreamTestDataFilePath))![0];
        var textContent = chatMessageContents.FirstOrDefault();
        Assert.NotNull(textContent);
        Assert.Equal(testDataResponse.PromptFeedback!.BlockReason, textContent.Metadata!["PromptFeedbackBlockReason"]);
        Assert.Equal(testDataResponse.Candidates[0].FinishReason, textContent.Metadata!["FinishReason"]);
        Assert.Equal(testDataResponse.Candidates[0].Index, textContent.Metadata!["Index"]);
        Assert.Equal(testDataResponse.Candidates[0].TokenCount, textContent.Metadata!["TokenCount"]);
        Assert.True((textContent.Metadata!["SafetyRatings"] as IEnumerable<object>)!.Count()
                    == testDataResponse.Candidates[0].SafetyRatings.Count);
        Assert.True((textContent.Metadata!["PromptFeedbackSafetyRatings"] as IEnumerable<object>)!.Count()
                    == testDataResponse.PromptFeedback.SafetyRatings.Count);
    }

    [Fact]
    public async Task ShouldReturnResponseWithModelIdAsync()
    {
        // Arrange
        string modelId = "fake-model";
        var client = new GeminiClient(modelId, "fake-api-key", this._httpClient);
        var chatHistory = CreateChatHistory();

        // Act
        var chatMessageContents =
            await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        var chatMessageContent = chatMessageContents.FirstOrDefault();
        Assert.NotNull(chatMessageContent);
        Assert.Equal(modelId, chatMessageContent.ModelId);
    }

    [Fact]
    public async Task ShouldReturnResponseWithValidInnerContentAsync()
    {
        // Arrange
        var client = new GeminiClient("fake-model", "fake-api-key", this._httpClient);
        var chatHistory = CreateChatHistory();

        // Act
        var chatMessageContents =
            await client.StreamGenerateChatMessageAsync(chatHistory).ToListAsync();

        // Assert
        string testDataResponseJson = JsonSerializer.Serialize(JsonSerializer.Deserialize<IList<GeminiResponse>>(
            await File.ReadAllTextAsync(StreamTestDataFilePath))![0].Candidates[0]);
        var textContent = chatMessageContents.FirstOrDefault();
        Assert.NotNull(textContent);
        Assert.Equal(testDataResponseJson, JsonSerializer.Serialize(textContent.InnerContent));
    }

    [Fact]
    public async Task ShouldUsePromptExecutionSettingsAsync()
    {
        // Arrange
        var client = new GeminiClient("fake-model", "fake-api-key", this._httpClient);
        var chatHistory = CreateChatHistory();
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 102,
            Temperature = 0.45,
            TopP = 0.6
        };

        // Act
        await client.StreamGenerateChatMessageAsync(chatHistory, executionSettings).ToListAsync();

        // Assert
        var geminiRequest = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(geminiRequest);
        Assert.Equal(executionSettings.MaxTokens, geminiRequest.Configuration!.MaxOutputTokens);
        Assert.Equal(executionSettings.Temperature, geminiRequest.Configuration!.Temperature);
        Assert.Equal(executionSettings.TopP, geminiRequest.Configuration!.TopP);
    }

    private static ChatHistory CreateChatHistory()
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        return chatHistory;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
