#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.GoogleVertexAI.Gemini;

public sealed class GeminiChatCompletionTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .Build();

    [Fact(Skip = "This test is for manual verification.")]
    public async Task GoogleAIGeminiChatGenerationAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var geminiService = new GoogleAIGeminiChatCompletionService(this.GoogleAIGetModel(), this.GoogleAIGetApiKey());

        // Act
        var response = await geminiService.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(response.Content);
        Assert.Contains("Large Language Model", response.Content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Brandon", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task GoogleAIGeminiChatStreamingAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and write a long story about my name.");

        var geminiService = new GoogleAIGeminiChatCompletionService(this.GoogleAIGetModel(), this.GoogleAIGetApiKey());

        // Act
        var response =
            await geminiService.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(response);
        Assert.True(response.Count > 1);
        Assert.DoesNotContain(response, chatMessage => string.IsNullOrEmpty(chatMessage.Content));
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task VertexAIGeminiChatGenerationAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and expand this abbreviation: LLM");

        var geminiService = new VertexAIGeminiChatCompletionService(
            model: this.VertexAIGetModel(),
            apiKey: this.VertexAIGetApiKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId());

        // Act
        var response = await geminiService.GetChatMessageContentAsync(chatHistory);

        // Assert
        Assert.NotNull(response.Content);
        Assert.Contains("Large Language Model", response.Content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Brandon", response.Content, StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task VertexAIGeminiChatStreamingAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Brandon, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("Call me by my name and write a long story about my name.");

        var geminiService = new VertexAIGeminiChatCompletionService(
            model: this.VertexAIGetModel(),
            apiKey: this.VertexAIGetApiKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId());

        // Act
        var response =
            await geminiService.GetStreamingChatMessageContentsAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(response);
        Assert.True(response.Count > 1);
        Assert.DoesNotContain(response, chatMessage => string.IsNullOrEmpty(chatMessage.Content));
    }

    private string GoogleAIGetModel() => this._configuration.GetSection("GoogleAI:Gemini:ModelId").Get<string>()!;
    private string GoogleAIGetApiKey() => this._configuration.GetSection("GoogleAI:Gemini:ApiKey").Get<string>()!;

    private string VertexAIGetModel() => this._configuration.GetSection("VertexAI:Gemini:ModelId").Get<string>()!;
    private string VertexAIGetApiKey() => this._configuration.GetSection("VertexAI:Gemini:ApiKey").Get<string>()!;
    private string VertexAIGetLocation() => this._configuration.GetSection("VertexAI:Gemini:Location").Get<string>()!;
    private string VertexAIGetProjectId() => this._configuration.GetSection("VertexAI:Gemini:ProjectId").Get<string>()!;
}
