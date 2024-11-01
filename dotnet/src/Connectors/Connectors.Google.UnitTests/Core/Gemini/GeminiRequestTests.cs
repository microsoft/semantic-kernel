﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini;

public sealed class GeminiRequestTests
{
    [Fact]
    public void FromPromptItReturnsWithConfiguration()
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
    public void FromPromptItReturnsWithSafetySettings()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            SafetySettings =
            [
                new(GeminiSafetyCategory.Derogatory, GeminiSafetyThreshold.BlockNone)
            ]
        };

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.SafetySettings);
        Assert.Equal(executionSettings.SafetySettings[0].Category, request.SafetySettings[0].Category);
        Assert.Equal(executionSettings.SafetySettings[0].Threshold, request.SafetySettings[0].Threshold);
    }

    [Fact]
    public void FromPromptItReturnsWithPrompt()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromPromptAndExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.Equal(prompt, request.Contents[0].Parts![0].Text);
    }

    [Fact]
    public void FromChatHistoryItReturnsWithConfiguration()
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
    public void FromChatHistoryItReturnsWithSafetySettings()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings
        {
            SafetySettings =
            [
                new(GeminiSafetyCategory.Derogatory, GeminiSafetyThreshold.BlockNone)
            ]
        };

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.SafetySettings);
        Assert.Equal(executionSettings.SafetySettings[0].Category, request.SafetySettings[0].Category);
        Assert.Equal(executionSettings.SafetySettings[0].Threshold, request.SafetySettings[0].Threshold);
    }

    [Fact]
    public void FromChatHistoryItReturnsWithChatHistory()
    {
        // Arrange
        string systemMessage = "system-message";
        var chatHistory = new ChatHistory(systemMessage);
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.SystemInstruction?.Parts);
        Assert.Single(request.SystemInstruction.Parts);
        Assert.Equal(request.SystemInstruction.Parts[0].Text, systemMessage);
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[1].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[2].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[3].Content, c.Parts![0].Text));
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[1].Role, c.Role),
            c => Assert.Equal(chatHistory[2].Role, c.Role),
            c => Assert.Equal(chatHistory[3].Role, c.Role));
    }

    [Fact]
    public void FromChatHistoryMultipleSystemMessagesItReturnsWithSystemMessages()
    {
        // Arrange
        string[] systemMessages = ["system-message", "system-message2", "system-message3", "system-message4"];
        var chatHistory = new ChatHistory(systemMessages[0]);
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddSystemMessage(systemMessages[1]);
        chatHistory.AddMessage(AuthorRole.System,
            [new TextContent(systemMessages[2]), new TextContent(systemMessages[3])]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.SystemInstruction?.Parts);
        Assert.All(systemMessages, msg => Assert.Contains(request.SystemInstruction.Parts, p => p.Text == msg));
    }

    [Fact]
    public void FromChatHistoryTextAsTextContentItReturnsWithChatHistory()
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
            c => Assert.Equal(chatHistory[0].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[1].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[2].Items.Cast<TextContent>().Single().Text, c.Parts![0].Text));
    }

    [Fact]
    public void FromChatHistoryImageAsImageContentItReturnsWithChatHistory()
    {
        // Arrange
        ReadOnlyMemory<byte> imageAsBytes = new byte[] { 0x00, 0x01, 0x02, 0x03 };
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems:
            [new ImageContent(new Uri("https://example-image.com/")) { MimeType = "image/png" }]);
        chatHistory.AddUserMessage(contentItems:
            [new ImageContent(imageAsBytes, "image/png")]);
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[1].Content, c.Parts![0].Text),
            c => Assert.Equal(chatHistory[2].Items.Cast<ImageContent>().Single().Uri,
                c.Parts![0].FileData!.FileUri),
            c => Assert.True(imageAsBytes.ToArray()
                .SequenceEqual(Convert.FromBase64String(c.Parts![0].InlineData!.InlineData))));
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
    public void FromChatHistoryCalledToolNotNullAddsFunctionResponse()
    {
        // Arrange
        ChatHistory chatHistory = [];
        var kvp = KeyValuePair.Create("sampleKey", "sampleValue");
        var expectedArgs = new JsonObject { [kvp.Key] = kvp.Value };
        var kernelFunction = KernelFunctionFactory.CreateFromMethod(() => "");
        var toolCall = new GeminiFunctionToolCall(new GeminiPart.FunctionCallPart { FunctionName = "function-name" });
        GeminiFunctionToolResult toolCallResult = new(toolCall, new FunctionResult(kernelFunction, expectedArgs));
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Tool, string.Empty, "modelId", toolCallResult));
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Single(request.Contents,
            c => c.Role == AuthorRole.Tool);
        Assert.Single(request.Contents,
            c => c.Parts![0].FunctionResponse is not null);
        Assert.Single(request.Contents,
            c => string.Equals(c.Parts![0].FunctionResponse!.FunctionName, toolCallResult.FullyQualifiedName, StringComparison.Ordinal));
        var args = request.Contents[0].Parts![0].FunctionResponse!.Response.Arguments;
        Assert.Equal(expectedArgs.ToJsonString(), args.ToJsonString());
    }

    [Fact]
    public void FromChatHistoryToolCallsNotNullAddsFunctionCalls()
    {
        // Arrange
        ChatHistory chatHistory = [];
        var kvp = KeyValuePair.Create("sampleKey", "sampleValue");
        var expectedArgs = new JsonObject { [kvp.Key] = kvp.Value };
        var toolCallPart = new GeminiPart.FunctionCallPart
        { FunctionName = "function-name", Arguments = expectedArgs };
        var toolCallPart2 = new GeminiPart.FunctionCallPart
        { FunctionName = "function2-name", Arguments = expectedArgs };
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Assistant, "tool-message", "model-id", functionsToolCalls: [toolCallPart]));
        chatHistory.Add(new GeminiChatMessageContent(AuthorRole.Assistant, "tool-message2", "model-id2", functionsToolCalls: [toolCallPart2]));
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);
        // Assert
        Assert.Collection(request.Contents,
            c => Assert.Equal(chatHistory[0].Role, c.Role),
            c => Assert.Equal(chatHistory[1].Role, c.Role));
        Assert.Collection(request.Contents,
            c => Assert.NotNull(c.Parts![0].FunctionCall),
            c => Assert.NotNull(c.Parts![0].FunctionCall));
        Assert.Collection(request.Contents,
            c => Assert.Equal(c.Parts![0].FunctionCall!.FunctionName, toolCallPart.FunctionName),
            c => Assert.Equal(c.Parts![0].FunctionCall!.FunctionName, toolCallPart2.FunctionName));
        Assert.Collection(request.Contents,
            c => Assert.Equal(expectedArgs.ToJsonString(),
                c.Parts![0].FunctionCall!.Arguments!.ToJsonString()),
            c => Assert.Equal(expectedArgs.ToJsonString(),
                c.Parts![0].FunctionCall!.Arguments!.ToJsonString()));
    }

    [Fact]
    public void AddFunctionToGeminiRequest()
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
    public void AddMultipleFunctionsToGeminiRequest()
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

    [Fact]
    public void AddChatMessageToRequest()
    {
        // Arrange
        ChatHistory chat = [];
        var request = GeminiRequest.FromChatHistoryAndExecutionSettings(chat, new GeminiPromptExecutionSettings());
        var message = new GeminiChatMessageContent(AuthorRole.User, "user-message", "model-id");

        // Act
        request.AddChatMessage(message);

        // Assert
        Assert.Single(request.Contents,
            c => string.Equals(message.Content, c.Parts![0].Text, StringComparison.Ordinal));
        Assert.Single(request.Contents,
            c => Equals(message.Role, c.Role));
    }

    private sealed class DummyContent(object? innerContent, string? modelId = null, IReadOnlyDictionary<string, object?>? metadata = null) :
        KernelContent(innerContent, modelId, metadata);
}
