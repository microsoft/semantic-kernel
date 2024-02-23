// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini;

public sealed class GeminiRequestTests
{
    [Fact]
    public void FromPromptItReturnsGeminiRequestWithConfiguration()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            Temperature = 1.5,
            MaxTokens = 10,
            TopP = 0.9,
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.Equal(executionSettings.Temperature, request.Configuration.Temperature);
        Assert.Equal(executionSettings.MaxTokens, request.Configuration.MaxOutputTokens);
        Assert.Equal(executionSettings.TopP, request.Configuration.TopP);
    }

    [Fact]
    public void FromPromptItReturnsGeminiRequestWithSafetySettings()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            SafetySettings = new List<GeminiSafetySetting>
            {
                new(GeminiSafetyCategory.Derogatory, GeminiSafetyThreshold.BlockNone)
            }
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.SafetySettings);
        Assert.Equal(executionSettings.SafetySettings[0].Category, request.SafetySettings[0].Category);
        Assert.Equal(executionSettings.SafetySettings[0].Threshold, request.SafetySettings[0].Threshold);
    }

    [Fact]
    public void FromPromptItReturnsGeminiRequestWithPrompt()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.Equal(prompt, request.Contents[0].Parts[0].Text);
    }

    [Fact]
    public void FromChatHistoryItReturnsGeminiRequestWithConfiguration()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings
        {
            Temperature = 1.5,
            MaxTokens = 10,
            TopP = 0.9,
        };

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.Equal(executionSettings.Temperature, request.Configuration.Temperature);
        Assert.Equal(executionSettings.MaxTokens, request.Configuration.MaxOutputTokens);
        Assert.Equal(executionSettings.TopP, request.Configuration.TopP);
    }

    [Fact]
    public void FromChatHistoryItReturnsGeminiRequestWithSafetySettings()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings
        {
            SafetySettings = new List<GeminiSafetySetting>
            {
                new(GeminiSafetyCategory.Derogatory, GeminiSafetyThreshold.BlockNone)
            }
        };

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.SafetySettings);
        Assert.Equal(executionSettings.SafetySettings[0].Category, request.SafetySettings[0].Category);
        Assert.Equal(executionSettings.SafetySettings[0].Threshold, request.SafetySettings[0].Threshold);
    }

    [Fact]
    public void FromChatHistoryItReturnsGeminiRequestWithChatHistory()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Content, c.Parts[0].Text),
            c => Assert.Equal(chatHistory[1].Content, c.Parts[0].Text),
            c => Assert.Equal(chatHistory[2].Content, c.Parts[0].Text));
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Role, c.Role),
            c => Assert.Equal(chatHistory[1].Role, c.Role),
            c => Assert.Equal(chatHistory[2].Role, c.Role));
    }

    [Fact]
    public void FromChatHistoryTextAsTextContentItReturnsGeminiRequestWithChatHistory()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems: [new TextContent("user-message2")]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Content, c.Parts[0].Text),
            c => Assert.Equal(chatHistory[1].Content, c.Parts[0].Text),
            c => Assert.Equal(chatHistory[2].Items!.Cast<TextContent>().Single().Text, c.Parts[0].Text));
    }

    [Fact]
    public void FromChatHistoryImageAsImageContentItReturnsGeminiRequestWithChatHistory()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems:
            [new ImageContent(new Uri("https://example-image.com/"), metadata: new Dictionary<string, object?> { ["mimeType"] = "value" })]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Content, c.Parts[0].Text),
            c => Assert.Equal(chatHistory[1].Content, c.Parts[0].Text),
            c => Assert.Equal(chatHistory[2].Items!.Cast<ImageContent>().Single().Uri, c.Parts[0].FileData!.FileUri));
    }

    [Fact]
    public void FromChatHistoryUnsupportedContentItThrowsNotSupportedException()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems: [new DummyContent("unsupported-content")]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        void Act() => GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Throws<NotSupportedException>(Act);
    }

    [Fact]
    public void AddFunctionItAddsFunctionToGeminiRequest()
    {
        // Arrange
        var request = new GeminiRequest();
        var function = new GeminiFunction("function-name", "function-description", "desc", null, null);

        // Act
        request.AddFunction(function);

        // Assert
        Assert.Collection(request.Tools!.Single().Functions,
            func => Assert.Equivalent(function.ToFunctionDeclaration(), func, strict: true));
    }

    [Fact]
    public void AddMultipleFunctionsItAddsFunctionsToGeminiRequest()
    {
        // Arrange
        var request = new GeminiRequest();
        var functions = new[]
        {
            new GeminiFunction("function-name", "function-description", "desc", null, null),
            new GeminiFunction("function-name2", "function-description2", "desc2", null, null)
        };

        // Act
        request.AddFunction(functions[0]);
        request.AddFunction(functions[1]);

        // Assert
        Assert.Collection(request.Tools!.Single().Functions,
            func => Assert.Equivalent(functions[0].ToFunctionDeclaration(), func, strict: true),
            func => Assert.Equivalent(functions[1].ToFunctionDeclaration(), func, strict: true));
    }

    private sealed class DummyContent : KernelContent
    {
        public DummyContent(object? innerContent, string? modelId = null, IReadOnlyDictionary<string, object?>? metadata = null)
            : base(innerContent, modelId, metadata) { }
    }
}
