﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
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
}
