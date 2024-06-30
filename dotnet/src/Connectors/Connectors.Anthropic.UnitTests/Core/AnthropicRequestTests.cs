// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Core;

public sealed class AnthropicRequestTests
{
    [Fact]
    public void FromChatHistoryItReturnsClaudeRequestWithConfiguration()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new AnthropicPromptExecutionSettings
        {
            Temperature = 1.5,
            MaxTokens = 10,
            TopP = 0.9f,
            ModelId = "claude"
        };

        // Act
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Equal(executionSettings.Temperature, request.Temperature);
        Assert.Equal(executionSettings.MaxTokens, request.MaxTokens);
        Assert.Equal(executionSettings.TopP, request.TopP);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void FromChatHistoryItReturnsClaudeRequestWithValidStreamingMode(bool streamMode)
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new AnthropicPromptExecutionSettings
        {
            Temperature = 1.5,
            MaxTokens = 10,
            TopP = 0.9f,
            ModelId = "claude"
        };

        // Act
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings, streamMode);

        // Assert
        Assert.Equal(streamMode, request.Stream);
    }

    [Fact]
    public void FromChatHistoryItReturnsClaudeRequestWithChatHistory()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage("user-message2");
        var executionSettings = new AnthropicPromptExecutionSettings
        {
            ModelId = "claude",
            MaxTokens = 128,
        };

        // Act
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.All(request.Messages, c => Assert.IsType<AnthropicTextContent>(c.Contents[0]));
        Assert.Collection(request.Messages,
            c => Assert.Equal(chatHistory[0].Content, ((AnthropicTextContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[1].Content, ((AnthropicTextContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[2].Content, ((AnthropicTextContent)c.Contents[0]).Text));
        Assert.Collection(request.Messages,
            c => Assert.Equal(chatHistory[0].Role, c.Role),
            c => Assert.Equal(chatHistory[1].Role, c.Role),
            c => Assert.Equal(chatHistory[2].Role, c.Role));
    }

    [Fact]
    public void FromChatHistoryTextAsTextContentItReturnsClaudeRequestWithChatHistory()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems: [new TextContent("user-message2")]);
        var executionSettings = new AnthropicPromptExecutionSettings
        {
            ModelId = "claude",
            MaxTokens = 128,
        };

        // Act
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.All(request.Messages, c => Assert.IsType<AnthropicTextContent>(c.Contents[0]));
        Assert.Collection(request.Messages,
            c => Assert.Equal(chatHistory[0].Content, ((AnthropicTextContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[1].Content, ((AnthropicTextContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[2].Items.Cast<TextContent>().Single().Text, ((AnthropicTextContent)c.Contents[0]).Text));
    }

    [Fact]
    public void FromChatHistoryImageAsImageContentItReturnsClaudeRequestWithChatHistory()
    {
        // Arrange
        ReadOnlyMemory<byte> imageAsBytes = new byte[] { 0x00, 0x01, 0x02, 0x03 };
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems:
            [new ImageContent(imageAsBytes, "image/png")]);
        var executionSettings = new AnthropicPromptExecutionSettings
        {
            ModelId = "claude",
            MaxTokens = 128,
        };

        // Act
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Collection(request.Messages,
            c => Assert.IsType<AnthropicTextContent>(c.Contents[0]),
            c => Assert.IsType<AnthropicTextContent>(c.Contents[0]),
            c => Assert.IsType<AnthropicImageContent>(c.Contents[0]));
        Assert.Collection(request.Messages,
            c => Assert.Equal(chatHistory[0].Content, ((AnthropicTextContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[1].Content, ((AnthropicTextContent)c.Contents[0]).Text),
            c =>
            {
                Assert.Equal(chatHistory[2].Items.Cast<ImageContent>().Single().MimeType, ((AnthropicImageContent)c.Contents[0]).Source.MediaType);
                Assert.True(imageAsBytes.ToArray().SequenceEqual(Convert.FromBase64String(((AnthropicImageContent)c.Contents[0]).Source.Data)));
            });
    }

    [Fact]
    public void FromChatHistoryUnsupportedContentItThrowsNotSupportedException()
    {
        // Arrange
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("user-message");
        chatHistory.AddAssistantMessage("assist-message");
        chatHistory.AddUserMessage(contentItems: [new DummyContent("unsupported-content")]);
        var executionSettings = new AnthropicPromptExecutionSettings
        {
            ModelId = "claude",
            MaxTokens = 128,
        };

        // Act
        void Act() => AnthropicRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Throws<NotSupportedException>(Act);
    }

    [Fact]
    public void AddFunctionItAddsFunctionToClaudeRequest()
    {
        // Arrange
        var request = new AnthropicRequest();
        var function = new AnthropicFunction("function-name", "function-description", "desc", null, null);

        // Act
        request.AddFunction(function);

        // Assert
        Assert.NotNull(request.Tools);
        Assert.Collection(request.Tools,
            func => Assert.Equivalent(function.ToFunctionDeclaration(), func, strict: true));
    }

    [Fact]
    public void AddMultipleFunctionsItAddsFunctionsToClaudeRequest()
    {
        // Arrange
        var request = new AnthropicRequest();
        var functions = new[]
        {
            new AnthropicFunction("function-name", "function-description", "desc", null, null),
            new AnthropicFunction("function-name2", "function-description2", "desc2", null, null)
        };

        // Act
        request.AddFunction(functions[0]);
        request.AddFunction(functions[1]);

        // Assert
        Assert.NotNull(request.Tools);
        Assert.Collection(request.Tools,
            func => Assert.Equivalent(functions[0].ToFunctionDeclaration(), func, strict: true),
            func => Assert.Equivalent(functions[1].ToFunctionDeclaration(), func, strict: true));
    }

    [Fact]
    public void FromChatHistoryCalledToolNotNullAddsFunctionResponse()
    {
        // Arrange
        ChatHistory chatHistory = [];
        var kvp = KeyValuePair.Create("sampleKey", "sampleValue");
        var expectedArgs = new JsonObject { [kvp.Key] = kvp.Value };
        var kernelFunction = KernelFunctionFactory.CreateFromMethod(() => "");
        var functionResult = new FunctionResult(kernelFunction, expectedArgs);
        var toolCall = new AnthropicFunctionToolCall(new AnthropicToolCallContent { ToolId = "any uid", FunctionName = "function-name" });
        AnthropicFunctionToolResult toolCallResult = new(toolCall, functionResult, toolCall.ToolUseId);
        chatHistory.Add(new AnthropicChatMessageContent(AuthorRole.Assistant, string.Empty, "modelId", toolCallResult));
        var executionSettings = new AnthropicPromptExecutionSettings { ModelId = "model-id", MaxTokens = 128 };

        // Act
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.Single(request.Messages,
            c => c.Role == AuthorRole.Assistant);
        Assert.Single(request.Messages,
            c => c.Contents[0] is AnthropicToolResultContent);
        Assert.Single(request.Messages,
            c => c.Contents[0] is AnthropicToolResultContent toolResult
                 && string.Equals(toolResult.ToolId, toolCallResult.ToolUseId, StringComparison.Ordinal)
                 && toolResult.Content is AnthropicTextContent textContent
                 && string.Equals(functionResult.ToString(), textContent.Text, StringComparison.Ordinal));
    }

    [Fact]
    public void FromChatHistoryToolCallsNotNullAddsFunctionCalls()
    {
        // Arrange
        ChatHistory chatHistory = [];
        var kvp = KeyValuePair.Create("sampleKey", "sampleValue");
        var expectedArgs = new JsonObject { [kvp.Key] = kvp.Value };
        var toolCallPart = new AnthropicToolCallContent
        { ToolId = "any uid1", FunctionName = "function-name", Arguments = expectedArgs };
        var toolCallPart2 = new AnthropicToolCallContent
        { ToolId = "any uid2", FunctionName = "function2-name", Arguments = expectedArgs };
        chatHistory.Add(new AnthropicChatMessageContent(AuthorRole.Assistant, "tool-message", "model-id", functionsToolCalls: [toolCallPart]));
        chatHistory.Add(new AnthropicChatMessageContent(AuthorRole.Assistant, "tool-message2", "model-id2", functionsToolCalls: [toolCallPart2]));
        var executionSettings = new AnthropicPromptExecutionSettings { ModelId = "model-id", MaxTokens = 128 };

        // Act
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);
        // Assert
        Assert.Collection(request.Messages,
            c => Assert.Equal(chatHistory[0].Role, c.Role),
            c => Assert.Equal(chatHistory[1].Role, c.Role));
        Assert.Collection(request.Messages,
            c => Assert.IsType<AnthropicToolCallContent>(c.Contents[0]),
            c => Assert.IsType<AnthropicToolCallContent>(c.Contents[0]));
        Assert.Collection(request.Messages,
            c =>
            {
                Assert.Equal(((AnthropicToolCallContent)c.Contents[0]).FunctionName, toolCallPart.FunctionName);
                Assert.Equal(((AnthropicToolCallContent)c.Contents[0]).ToolId, toolCallPart.ToolId);
            },
            c =>
            {
                Assert.Equal(((AnthropicToolCallContent)c.Contents[0]).FunctionName, toolCallPart2.FunctionName);
                Assert.Equal(((AnthropicToolCallContent)c.Contents[0]).ToolId, toolCallPart2.ToolId);
            });
        Assert.Collection(request.Messages,
            c => Assert.Equal(expectedArgs.ToJsonString(),
                ((AnthropicToolCallContent)c.Contents[0]).Arguments!.ToJsonString()),
            c => Assert.Equal(expectedArgs.ToJsonString(),
                ((AnthropicToolCallContent)c.Contents[0]).Arguments!.ToJsonString()));
    }

    [Fact]
    public void AddChatMessageToRequestItAddsChatMessageToGeminiRequest()
    {
        // Arrange
        ChatHistory chat = [];
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chat, new AnthropicPromptExecutionSettings { ModelId = "model-id", MaxTokens = 128 });
        var message = new AnthropicChatMessageContent(AuthorRole.User, "user-message", "model-id");

        // Act
        request.AddChatMessage(message);

        // Assert
        Assert.Single(request.Messages,
            c => c.Contents[0] is AnthropicTextContent content && string.Equals(message.Content, content.Text, StringComparison.Ordinal));
        Assert.Single(request.Messages,
            c => Equals(message.Role, c.Role));
    }

    private sealed class DummyContent : KernelContent
    {
        public DummyContent(object? innerContent, string? modelId = null, IReadOnlyDictionary<string, object?>? metadata = null)
            : base(innerContent, modelId, metadata) { }
    }
}
