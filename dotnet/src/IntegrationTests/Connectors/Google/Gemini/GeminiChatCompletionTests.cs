// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Newtonsoft.Json.Linq;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Google.Gemini;

public sealed class GeminiChatCompletionTests(ITestOutputHelper output) : TestsBase(output)
{
    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationReturnsValidResponseAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(response.Content);
        this.Output.WriteLine(response.Content);
        Assert.Contains("Large Language Model", response.Content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Brandon", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatStreamingReturnsValidResponseAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and write a long story about my name.");

        var sut = this.GetChatService(serviceType);

        // Act
        var response =
            await sut.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(response);
        Assert.True(response.Count > 1);
        var message = string.Concat(response.Select(c => c.Content));
        Assert.False(string.IsNullOrWhiteSpace(message));
        this.Output.WriteLine(message);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationOnlyAssistantMessagesReturnsValidResponseAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddAssistantMessage("I'm Brandon, I'm very thirsty");
        chatHistory.AddAssistantMessage("Could you help me get some...");

        var sut = this.GetChatService(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(response.Content);
        this.Output.WriteLine(response.Content);
        string[] resultWords = ["drink", "water", "tea", "coffee", "juice", "soda"];
        Assert.Contains(resultWords, word => response.Content.Contains(word, StringComparison.OrdinalIgnoreCase));
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatStreamingOnlyAssistantMessagesReturnsValidResponseAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddAssistantMessage("I'm Brandon, I'm very thirsty");
        chatHistory.AddAssistantMessage("Could you help me get some...");

        var sut = this.GetChatService(serviceType);

        // Act
        var response =
            await sut.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(response);
        Assert.True(response.Count > 1);
        var message = string.Concat(response.Select(c => c.Content));
        this.Output.WriteLine(message);
        string[] resultWords = ["drink", "water", "tea", "coffee", "juice", "soda"];
        Assert.Contains(resultWords, word => message.Contains(word, StringComparison.OrdinalIgnoreCase));
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationWithSystemMessagesAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory("You are helpful assistant. Your name is Roger.");
        chatHistory.AddSystemMessage("You know ACDD equals 1520");
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Tell me your name and the value of ACDD.");

        var sut = this.GetChatService(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(response.Content);
        this.Output.WriteLine(response.Content);
        Assert.Contains("1520", response.Content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Roger", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationWithCachedContentAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Finish this sentence: He knew the sea’s...");

        // Setup initial cached content
        var cachedContentJson = File.ReadAllText(Path.Combine("Resources", "gemini_cached_content.json"))
            .Replace("{{project}}", this.VertexAI.ProjectId!)
            .Replace("{{location}}", this.VertexAI.Location!)
            .Replace("{{model}}", this.VertexAI.Gemini.ModelId!);

        var cachedContentName = string.Empty;

        using (var httpClient = new HttpClient()
        {
            DefaultRequestHeaders = { Authorization = new("Bearer", this.VertexAI.BearerKey) }
        })
        {
            using (var content = new StringContent(cachedContentJson, Encoding.UTF8, "application/json"))
            {
                using (var httpResponse = await httpClient.PostAsync(
                new Uri($"https://{this.VertexAI.Location}-aiplatform.googleapis.com/v1beta1/projects/{this.VertexAI.ProjectId!}/locations/{this.VertexAI.Location}/cachedContents"),
                content))
                {
                    httpResponse.EnsureSuccessStatusCode();

                    var responseString = await httpResponse.Content.ReadAsStringAsync();
                    var responseJson = JObject.Parse(responseString);

                    cachedContentName = responseJson?["name"]?.ToString();

                    Assert.NotNull(cachedContentName);
                }
            }
        }

        var sut = this.GetChatService(serviceType, isBeta: true);

        // Act
        var response = await sut.GetChatMessageContentAsync(
            chatHistory,
            new GeminiPromptExecutionSettings
            {
                CachedContent = cachedContentName
            });

        // Assert
        Assert.NotNull(response.Content);
        this.Output.WriteLine(response.Content);
        Assert.Contains("capriciousness", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatStreamingWithSystemMessagesAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory("You are helpful assistant. Your name is Roger.");
        chatHistory.AddSystemMessage("You know ACDD equals 1520");
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Tell me your name and the value of ACDD.");

        var sut = this.GetChatService(serviceType);

        // Act
        var response =
            await sut.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(response);
        Assert.True(response.Count > 1);
        var message = string.Concat(response.Select(c => c.Content));
        this.Output.WriteLine(message);
        Assert.Contains("1520", message, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Roger", message, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationVisionBinaryDataAsync(ServiceType serviceType)
    {
        // Arrange
        Memory<byte> image = await File.ReadAllBytesAsync("./TestData/test_image_001.jpg");
        var chatHistory = new ChatHistory();
        var messageContent = new ChatMessageContent(AuthorRole.User, items:
        [
            new TextContent("This is an image with a car. Which color is it? You can chose from red, blue, green, and yellow"),
            new ImageContent(image, "image/jpeg")
        ]);
        chatHistory.Add(messageContent);

        var sut = this.GetChatServiceWithVision(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(response.Content);
        this.Output.WriteLine(response.Content);
        Assert.Contains("green", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatStreamingVisionBinaryDataAsync(ServiceType serviceType)
    {
        // Arrange
        Memory<byte> image = await File.ReadAllBytesAsync("./TestData/test_image_001.jpg");
        var chatHistory = new ChatHistory();
        var messageContent = new ChatMessageContent(AuthorRole.User, items:
        [
            new TextContent("This is an image with a car. Which color is it? You can chose from red, blue, green, and yellow"),
            new ImageContent(image, "image/jpeg")
        ]);
        chatHistory.Add(messageContent);

        var sut = this.GetChatServiceWithVision(serviceType);

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(responses);
        var message = string.Concat(responses.Select(c => c.Content));
        Assert.False(string.IsNullOrWhiteSpace(message));
        this.Output.WriteLine(message);
        Assert.Contains("green", message, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "Currently passing image by URI are not supported by GoogleAI.")]
    [InlineData(ServiceType.VertexAI, Skip = "Needs setup image in VertexAI storage.")]
    public async Task ChatGenerationVisionUriAsync(ServiceType serviceType)
    {
        // Arrange
        Uri imageUri = new("gs://generativeai-downloads/images/scones.jpg"); // needs setup
        var chatHistory = new ChatHistory();
        var messageContent = new ChatMessageContent(AuthorRole.User, items:
        [
            new TextContent("This is an image with a car. Which color is it? You can chose from red, blue, green, and yellow"),
            new ImageContent(imageUri) { MimeType = "image/jpeg" }
        ]);
        chatHistory.Add(messageContent);

        var sut = this.GetChatServiceWithVision(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(response.Content);
        this.Output.WriteLine(response.Content);
        Assert.Contains("green", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "Currently passing image by URI are not supported by GoogleAI.")]
    [InlineData(ServiceType.VertexAI, Skip = "Needs setup image in VertexAI storage.")]
    public async Task ChatStreamingVisionUriAsync(ServiceType serviceType)
    {
        // Arrange
        Uri imageUri = new("gs://generativeai-downloads/images/scones.jpg"); // needs setup
        var chatHistory = new ChatHistory();
        var messageContent = new ChatMessageContent(AuthorRole.User, items:
        [
            new TextContent("This is an image with a car. Which color is it? You can chose from red, blue, green, and yellow"),
            new ImageContent(imageUri) { MimeType = "image/jpeg" }
        ]);
        chatHistory.Add(messageContent);

        var sut = this.GetChatServiceWithVision(serviceType);

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(responses);
        var message = string.Concat(responses.Select(c => c.Content));
        Assert.False(string.IsNullOrWhiteSpace(message));
        this.Output.WriteLine(message);
        Assert.Contains("green", message, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationAudioBinaryDataAsync(ServiceType serviceType)
    {
        // Arrange
        Memory<byte> audio = await File.ReadAllBytesAsync(Path.Combine("TestData", "test_audio.wav"));
        var chatHistory = new ChatHistory();
        var messageContent = new ChatMessageContent(AuthorRole.User, items:
        [
            new TextContent("Transcribe this audio"),
            new AudioContent(audio, "audio/wav")
        ]);
        chatHistory.Add(messageContent);

        var sut = this.GetChatServiceWithVision(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(response.Content);
        this.Output.WriteLine(response.Content);
        Assert.Contains("the sun rises", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationAudioUriAsync(ServiceType serviceType)
    {
        // Arrange
        Uri audioUri = new("gs://cloud-samples-data/speech/brooklyn_bridge.flac"); // needs setup
        var chatHistory = new ChatHistory();
        var messageContent = new ChatMessageContent(AuthorRole.User, items:
        [
            new TextContent("Transcribe this audio"),
            new AudioContent(audioUri) { MimeType = "audio/flac" }
        ]);
        chatHistory.Add(messageContent);

        var sut = this.GetChatServiceWithVision(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(response.Content);
        this.Output.WriteLine(response.Content);
        Assert.Contains("brooklyn bridge", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "Currently GoogleAI always returns zero tokens.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationReturnsUsedTokensAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        var geminiMetadata = response.Metadata as GeminiMetadata;
        Assert.NotNull(geminiMetadata);
        foreach ((string? key, object? value) in geminiMetadata)
        {
            this.Output.WriteLine($"{key}: {JsonSerializer.Serialize(value)}");
        }

        Assert.True(geminiMetadata.TotalTokenCount > 0);
        Assert.True(geminiMetadata.CandidatesTokenCount > 0);
        Assert.True(geminiMetadata.PromptTokenCount > 0);
        Assert.True(geminiMetadata.CurrentCandidateTokenCount > 0);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "Currently GoogleAI always returns zero tokens.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatStreamingReturnsUsedTokensAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(serviceType);

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        var geminiMetadata = responses.Last().Metadata as GeminiMetadata;
        Assert.NotNull(geminiMetadata);
        this.Output.WriteLine($"TotalTokenCount: {geminiMetadata.TotalTokenCount}");
        this.Output.WriteLine($"CandidatesTokenCount: {geminiMetadata.CandidatesTokenCount}");
        this.Output.WriteLine($"PromptTokenCount: {geminiMetadata.PromptTokenCount}");
        this.Output.WriteLine($"CurrentCandidateTokenCount: {geminiMetadata.CurrentCandidateTokenCount}");
        Assert.True(geminiMetadata.TotalTokenCount > 0);
        Assert.True(geminiMetadata.CandidatesTokenCount > 0);
        Assert.True(geminiMetadata.PromptTokenCount > 0);
        Assert.True(geminiMetadata.CurrentCandidateTokenCount > 0);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationReturnsPromptFeedbackAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        var geminiMetadata = response.Metadata as GeminiMetadata;
        Assert.NotNull(geminiMetadata);
        this.Output.WriteLine($"PromptFeedbackBlockReason: {geminiMetadata.PromptFeedbackBlockReason}");
        this.Output.WriteLine($"PromptFeedbackSafetyRatings: {JsonSerializer.Serialize(geminiMetadata.PromptFeedbackSafetyRatings)}");
        Assert.NotNull(geminiMetadata.PromptFeedbackSafetyRatings);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatStreamingReturnsPromptFeedbackAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(serviceType);

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        var geminiMetadata = responses.First().Metadata as GeminiMetadata;
        Assert.NotNull(geminiMetadata);
        this.Output.WriteLine($"PromptFeedbackBlockReason: {geminiMetadata.PromptFeedbackBlockReason}");
        this.Output.WriteLine($"PromptFeedbackSafetyRatings: {JsonSerializer.Serialize(geminiMetadata.PromptFeedbackSafetyRatings)}");
        Assert.NotNull(geminiMetadata.PromptFeedbackSafetyRatings);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationReturnsStopFinishReasonAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        var geminiMetadata = response.Metadata as GeminiMetadata;
        Assert.NotNull(geminiMetadata);
        this.Output.WriteLine($"FinishReason: {geminiMetadata.FinishReason}");
        Assert.Equal(GeminiFinishReason.Stop, geminiMetadata.FinishReason);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatStreamingReturnsStopFinishReasonAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(serviceType);

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        var geminiMetadata = responses.Last().Metadata as GeminiMetadata;
        Assert.NotNull(geminiMetadata);
        this.Output.WriteLine($"FinishReason: {geminiMetadata.FinishReason}");
        Assert.Equal(GeminiFinishReason.Stop, geminiMetadata.FinishReason);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatGenerationReturnsResponseSafetyRatingsAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(serviceType);

        // Act
        var response = await sut.GetChatMessageContentAsync(chatHistory);

        // Assert
        var geminiMetadata = response.Metadata as GeminiMetadata;
        Assert.NotNull(geminiMetadata);
        this.Output.WriteLine($"ResponseSafetyRatings: {JsonSerializer.Serialize(geminiMetadata.ResponseSafetyRatings)}");
        Assert.NotNull(geminiMetadata.ResponseSafetyRatings);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task ChatStreamingReturnsResponseSafetyRatingsAsync(ServiceType serviceType)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(serviceType);

        // Act
        var responses = await sut.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        var geminiMetadata = responses.Last().Metadata as GeminiMetadata;
        Assert.NotNull(geminiMetadata);
        this.Output.WriteLine($"ResponseSafetyRatings: {JsonSerializer.Serialize(geminiMetadata.ResponseSafetyRatings)}");
        Assert.NotNull(geminiMetadata.ResponseSafetyRatings);
    }

    [RetryFact(Skip = "This test is for manual verification.")]
    public async Task GoogleAIChatReturnsResponseWorksWithThinkingBudgetAsync()
    {
        // Arrange
        var modelId = "gemini-2.5-pro-exp-03-25";
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var sut = this.GetChatService(ServiceType.GoogleAI, isBeta: true, overrideModelId: modelId);
        var settings = new GeminiPromptExecutionSettings { ThinkingConfig = new() { ThinkingBudget = 2000 } };

        // Act
        var streamResponses = await sut.GetStreamingChatMessageContentsAsync(chatHistory, settings).ToListAsync();
        var responses = await sut.GetChatMessageContentsAsync(chatHistory, settings);

        // Assert
        Assert.NotNull(streamResponses[0].Content);
        Assert.NotNull(responses[0].Content);
    }
}
