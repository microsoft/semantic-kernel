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
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Gemini;
using Microsoft.SemanticKernel.Connectors.Gemini.Core;
using SemanticKernel.UnitTests;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests.Core;

public sealed class GeminiClientTextGenerationTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string TestDataFilePath = "./TestData/completion_one_response.json";

    public GeminiClientTextGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(
            File.ReadAllText(TestDataFilePath));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldUseUserAgentAsync()
    {
        // Arrange
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        await client.GenerateTextAsync("fake-text");

        // Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("User-Agent"));
        IEnumerable<string> values = this._messageHandlerStub.RequestHeaders!.GetValues("User-Agent");
        string? value = values.SingleOrDefault();
        Assert.Equal("Semantic-Kernel", value);
    }

    [Fact]
    public async Task ShouldUseSpecifiedModelAsync()
    {
        // Arrange
        string modelId = "fake-model";
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        await client.GenerateTextAsync("fake-text");

        // Assert
        Assert.Contains(modelId, this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldUseSpecifiedApiKeyAsync()
    {
        // Arrange
        string fakeAPIKey = "fake-api-key";
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        await client.GenerateTextAsync("fake-text");

        // Assert
        Assert.Contains(fakeAPIKey, this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldUseBaseEndpointAsync()
    {
        // Arrange
        var baseEndPoint = GeminiEndpoints.BaseEndpoint.AbsoluteUri;
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        await client.GenerateTextAsync("fake-text");

        // Assert
        Assert.StartsWith(baseEndPoint, this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        // Arrange
        string prompt = "fake-prompt";
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        await client.GenerateTextAsync(prompt);

        // Assert
        GeminiRequest? request = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Equal(prompt, request.Contents[0].Parts[0].Text);
    }

    [Fact]
    public async Task ShouldReturnValidModelTextResponseAsync()
    {
        // Arrange
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        IReadOnlyList<TextContent> textContents = await client.GenerateTextAsync("fake-text");

        // Assert
        GeminiResponse testDataResponse = JsonSerializer.Deserialize<GeminiResponse>(
            await File.ReadAllTextAsync(TestDataFilePath))!;
        var textContent = textContents.SingleOrDefault();
        Assert.NotNull(textContent);
        Assert.Equal(testDataResponse.Candidates[0].Content.Parts[0].Text, textContent.Text);
    }

    [Fact]
    public async Task ShouldReturnValidGeminiMetadataAsync()
    {
        // Arrange
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        IReadOnlyList<TextContent> textContents = await client.GenerateTextAsync("fake-text");

        // Assert
        GeminiResponse testDataResponse = JsonSerializer.Deserialize<GeminiResponse>(
            await File.ReadAllTextAsync(TestDataFilePath))!;
        var testDataCandidate = testDataResponse.Candidates[0];
        var textContent = textContents.SingleOrDefault();
        Assert.NotNull(textContent);
        var metadata = textContent.Metadata as GeminiMetadata;
        Assert.NotNull(metadata);
        Assert.Equal(testDataResponse.PromptFeedback!.BlockReason, metadata.PromptFeedbackBlockReason);
        Assert.Equal(testDataCandidate.FinishReason, metadata.FinishReason);
        Assert.Equal(testDataCandidate.Index, metadata.Index);
        Assert.True(metadata.ResponseSafetyRatings!.Count
                    == testDataCandidate.SafetyRatings.Count);
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
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        IReadOnlyList<TextContent> textContents = await client.GenerateTextAsync("fake-text");
        // Assert
        GeminiResponse testDataResponse = JsonSerializer.Deserialize<GeminiResponse>(
            await File.ReadAllTextAsync(TestDataFilePath))!;
        var testDataCandidate = testDataResponse.Candidates[0];
        var textContent = textContents.SingleOrDefault();
        Assert.NotNull(textContent);
        var metadata = textContent.Metadata;
        Assert.NotNull(metadata);
        Assert.Equal(testDataResponse.PromptFeedback!.BlockReason, metadata[nameof(GeminiMetadata.PromptFeedbackBlockReason)]);
        Assert.Equal(testDataCandidate.FinishReason, metadata[nameof(GeminiMetadata.FinishReason)]);
        Assert.Equal(testDataCandidate.Index, metadata[nameof(GeminiMetadata.Index)]);
        var responseSafetyRatings = (IList<GeminiSafetyRating>)metadata[nameof(GeminiMetadata.ResponseSafetyRatings)]!;
        for (var i = 0; i < responseSafetyRatings.Count; i++)
        {
            Assert.Equal(testDataCandidate.SafetyRatings[i].Block, responseSafetyRatings[i].Block);
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
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        IReadOnlyList<TextContent> textContents = await client.GenerateTextAsync("fake-text");

        // Assert
        var textContent = textContents.SingleOrDefault();
        Assert.NotNull(textContent);
        Assert.Equal(geminiConfiguration.ModelId, textContent.ModelId);
    }

    [Fact]
    public async Task ShouldReturnResponseWithValidInnerContentAsync()
    {
        // Arrange
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);

        // Act
        IReadOnlyList<TextContent> textContents = await client.GenerateTextAsync("fake-text");

        // Assert
        string testDataResponseJson = JsonSerializer.Serialize(JsonSerializer.Deserialize<GeminiResponse>(
            await File.ReadAllTextAsync(TestDataFilePath))!.Candidates[0]);
        var textContent = textContents.SingleOrDefault();
        Assert.NotNull(textContent);
        Assert.Equal(testDataResponseJson, JsonSerializer.Serialize(textContent.InnerContent));
    }

    [Fact]
    public async Task ShouldUsePromptExecutionSettingsAsync()
    {
        // Arrange
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);
        var executionSettings = new GeminiPromptExecutionSettings()
        {
            MaxTokens = 102,
            Temperature = 0.45,
            TopP = 0.6
        };

        // Act
        await client.GenerateTextAsync("fake-text", executionSettings);

        // Assert
        var geminiRequest = JsonSerializer.Deserialize<GeminiRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(geminiRequest);
        Assert.Equal(executionSettings.MaxTokens, geminiRequest.Configuration!.MaxOutputTokens);
        Assert.Equal(executionSettings.Temperature, geminiRequest.Configuration!.Temperature);
        Assert.Equal(executionSettings.TopP, geminiRequest.Configuration!.TopP);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-15)]
    public async Task ShouldThrowArgumentExceptionIfExecutionSettingMaxTokensIsLessThanOneAsync(int? maxTokens)
    {
        // Arrange
        var geminiConfiguration = new GeminiConfiguration("fake-api-key") { ModelId = "fake-model" };
        var client = new GeminiClient(this._httpClient, geminiConfiguration);
        GeminiPromptExecutionSettings executionSettings = new()
        {
            MaxTokens = maxTokens
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(
            () => client.GenerateTextAsync("fake-text", executionSettings));
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
