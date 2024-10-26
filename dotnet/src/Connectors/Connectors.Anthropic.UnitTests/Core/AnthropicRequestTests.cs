// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Core;

public sealed class AnthropicRequestTests
{
    [Fact]
    public void FromChatHistoryItReturnsWithConfiguration()
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
    public void FromChatHistoryItReturnsWithValidStreamingMode(bool streamMode)
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
    public void FromChatHistoryItReturnsWithChatHistory()
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
        Assert.All(request.Messages, c => Assert.IsType<AnthropicContent>(c.Contents[0]));
        Assert.Collection(request.Messages,
            c => Assert.Equal(chatHistory[0].Content, ((AnthropicContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[1].Content, ((AnthropicContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[2].Content, ((AnthropicContent)c.Contents[0]).Text));
        Assert.Collection(request.Messages,
            c => Assert.Equal(chatHistory[0].Role, c.Role),
            c => Assert.Equal(chatHistory[1].Role, c.Role),
            c => Assert.Equal(chatHistory[2].Role, c.Role));
    }

    [Fact]
    public void FromChatHistoryTextAsTextContentItReturnsWithChatHistory()
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
        Assert.All(request.Messages, c => Assert.IsType<AnthropicContent>(c.Contents[0]));
        Assert.Collection(request.Messages,
            c => Assert.Equal(chatHistory[0].Content, ((AnthropicContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[1].Content, ((AnthropicContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[2].Items.Cast<TextContent>().Single().Text, ((AnthropicContent)c.Contents[0]).Text));
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
            c => Assert.IsType<AnthropicContent>(c.Contents[0]),
            c => Assert.IsType<AnthropicContent>(c.Contents[0]),
            c => Assert.IsType<AnthropicContent>(c.Contents[0]));
        Assert.Collection(request.Messages,
            c => Assert.Equal(chatHistory[0].Content, ((AnthropicContent)c.Contents[0]).Text),
            c => Assert.Equal(chatHistory[1].Content, ((AnthropicContent)c.Contents[0]).Text),
            c =>
            {
                Assert.Equal(chatHistory[2].Items.Cast<ImageContent>().Single().MimeType, ((AnthropicContent)c.Contents[0]).Source!.MediaType);
                Assert.True(imageAsBytes.ToArray().SequenceEqual(Convert.FromBase64String(((AnthropicContent)c.Contents[0]).Source!.Data!)));
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
    public void FromChatHistoryItReturnsWithSystemMessages()
    {
        // Arrange
        string[] systemMessages = ["system-message1", "system-message2", "system-message3", "system-message4"];
        ChatHistory chatHistory = new(systemMessages[0]);
        chatHistory.AddSystemMessage(systemMessages[1]);
        chatHistory.Add(new ChatMessageContent(AuthorRole.System,
            items: [new TextContent(systemMessages[2]), new TextContent(systemMessages[3])]));
        chatHistory.AddUserMessage("user-message");
        var executionSettings = new AnthropicPromptExecutionSettings
        {
            ModelId = "claude",
            MaxTokens = 128,
        };

        // Act
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chatHistory, executionSettings);

        // Assert
        Assert.NotNull(request.SystemPrompt);
        Assert.All(systemMessages, msg => Assert.Contains(msg, request.SystemPrompt, StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void AddChatMessageToRequestItAddsChatMessage()
    {
        // Arrange
        ChatHistory chat = [];
        var request = AnthropicRequest.FromChatHistoryAndExecutionSettings(chat, new AnthropicPromptExecutionSettings { ModelId = "model-id", MaxTokens = 128 });
        var message = new AnthropicChatMessageContent
        {
            Role = AuthorRole.User,
            Items = [new TextContent("user-message")],
            ModelId = "model-id",
            Encoding = Encoding.UTF8
        };

        // Act
        request.AddChatMessage(message);

        // Assert
        Assert.Single(request.Messages,
            c => c.Contents[0] is AnthropicContent content && string.Equals(message.Content, content.Text, StringComparison.Ordinal));
        Assert.Single(request.Messages,
            c => Equals(message.Role, c.Role));
    }

    private sealed class DummyContent(
        object? innerContent,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : KernelContent(innerContent, modelId, metadata);
}
