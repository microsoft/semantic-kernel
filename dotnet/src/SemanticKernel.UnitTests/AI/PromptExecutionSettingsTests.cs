// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.AI;

public class PromptExecutionSettingsTests
{
    [Fact]
    public void PromptExecutionSettingsCloneWorksAsExpected()
    {
        // Arrange
        string configPayload = """
        {
            "model_id": "gpt-3",
            "service_id": "service-1",
            "max_tokens": 60,
            "temperature": 0.5,
            "top_p": 0.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "function_choice_behavior": {
                "type": "auto",
                "functions": ["p1.f1"]
            }
        }
        """;
        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(configPayload);

        // Act
        var clone = executionSettings!.Clone();

        // Assert
        Assert.NotNull(clone);
        Assert.Equal(executionSettings.ModelId, clone.ModelId);
        Assert.Equivalent(executionSettings.ExtensionData, clone.ExtensionData);
        Assert.Equivalent(executionSettings.FunctionChoiceBehavior, clone.FunctionChoiceBehavior);
        Assert.Equal(executionSettings.ServiceId, clone.ServiceId);
    }

    [Fact]
    public void PromptExecutionSettingsSerializationWorksAsExpected()
    {
        // Arrange
        string configPayload = """
        {
            "model_id": "gpt-3",
            "service_id": "service-1",
            "max_tokens": 60,
            "temperature": 0.5,
            "top_p": 0.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        """;

        // Act
        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(configPayload);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("gpt-3", executionSettings.ModelId);
        Assert.Equal("service-1", executionSettings.ServiceId);
        Assert.Equal(60, ((JsonElement)executionSettings.ExtensionData!["max_tokens"]).GetInt32());
        Assert.Equal(0.5, ((JsonElement)executionSettings.ExtensionData!["temperature"]).GetDouble());
        Assert.Equal(0.0, ((JsonElement)executionSettings.ExtensionData!["top_p"]).GetDouble());
        Assert.Equal(0.0, ((JsonElement)executionSettings.ExtensionData!["presence_penalty"]).GetDouble());
    }

    [Fact]
    public void PromptExecutionSettingsFreezeWorksAsExpected()
    {
        // Arrange
        string configPayload = """
            {
                "max_tokens": 60,
                "temperature": 0.5,
                "top_p": 0.0,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0
            }
            """;
        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(configPayload);

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "gpt-4");
        Assert.NotNull(executionSettings.ExtensionData);
        Assert.Throws<NotSupportedException>(() => executionSettings.ExtensionData.Add("results_per_prompt", 2));
        Assert.Throws<NotSupportedException>(() => executionSettings.ExtensionData["temperature"] = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Auto());

        executionSettings!.Freeze(); // idempotent
        Assert.True(executionSettings.IsFrozen);
    }

    [Theory]
    [InlineData(true, false)] // System message only
    [InlineData(false, true)] // Developer message only
    [InlineData(true, true)]  // Both system and developer messages
    [InlineData(false, false)] // Neither message
    public async Task ChatClientExtensionsGetResponseAsyncCallsPrepareChatHistoryForRequest(bool addSystemMessage, bool addDeveloperMessage)
    {
        // Arrange
        var mockChatClient = new Mock<IChatClient>();
        var capturedMessages = new List<ChatMessage>();

        mockChatClient
            .Setup(x => x.GetResponseAsync(It.IsAny<IEnumerable<ChatMessage>>(), It.IsAny<ChatOptions>(), It.IsAny<CancellationToken>()))
            .Callback<IEnumerable<ChatMessage>, ChatOptions?, CancellationToken>((messages, options, ct) =>
            {
                capturedMessages.AddRange(messages);
            })
            .ReturnsAsync(new ChatResponse([new ChatMessage(ChatRole.Assistant, "Test response")]));

        var settings = new TestPromptExecutionSettings(addSystemMessage, addDeveloperMessage);
        var prompt = "Hello, world!";

        // Act
        await mockChatClient.Object.GetResponseAsync(prompt, settings);

        // Assert
        Assert.True(settings.PrepareChatHistoryWasCalled);

        // Verify the expected messages are present
        var expectedMessageCount = 1; // Original user message
        if (addSystemMessage)
        {
            expectedMessageCount++;
        }

        if (addDeveloperMessage)
        {
            expectedMessageCount++;
        }

        Assert.Equal(expectedMessageCount, capturedMessages.Count);

        var messageIndex = 0;
        if (addSystemMessage)
        {
            Assert.Equal(ChatRole.System, capturedMessages[messageIndex].Role);
            Assert.Equal("Test system message", capturedMessages[messageIndex].Text);
            messageIndex++;
        }

        if (addDeveloperMessage)
        {
            Assert.Equal(new ChatRole("developer"), capturedMessages[messageIndex].Role);
            Assert.Equal("Test developer message", capturedMessages[messageIndex].Text);
            messageIndex++;
        }

        // Original user message should be last
        Assert.Equal(ChatRole.User, capturedMessages[messageIndex].Role);
        Assert.Equal("Hello, world!", capturedMessages[messageIndex].Text);
    }

    [Theory]
    [InlineData(true, false)] // System message only
    [InlineData(false, true)] // Developer message only
    [InlineData(true, true)]  // Both system and developer messages
    [InlineData(false, false)] // Neither message
    public async Task ChatClientExtensionsGetStreamingResponseAsyncCallsPrepareChatHistoryForRequest(bool addSystemMessage, bool addDeveloperMessage)
    {
        // Arrange
        var mockChatClient = new Mock<IChatClient>();
        var capturedMessages = new List<ChatMessage>();

        mockChatClient
            .Setup(x => x.GetStreamingResponseAsync(It.IsAny<IEnumerable<ChatMessage>>(), It.IsAny<ChatOptions>(), It.IsAny<CancellationToken>()))
            .Callback<IEnumerable<ChatMessage>, ChatOptions?, CancellationToken>((messages, options, ct) =>
            {
                capturedMessages.AddRange(messages);
            })
            .Returns(new[] { new ChatResponseUpdate(ChatRole.Assistant, "Test streaming response") }.ToAsyncEnumerable());

        var settings = new TestPromptExecutionSettings(addSystemMessage, addDeveloperMessage);
        var prompt = "Hello, world!";

        // Act
        var responses = new List<ChatResponseUpdate>();
        await foreach (var response in mockChatClient.Object.GetStreamingResponseAsync(prompt, settings))
        {
            responses.Add(response);
        }

        // Assert
        Assert.True(settings.PrepareChatHistoryWasCalled);
        Assert.Single(responses);

        // Verify the expected messages are present
        var expectedMessageCount = 1; // Original user message
        if (addSystemMessage)
        {
            expectedMessageCount++;
        }

        if (addDeveloperMessage)
        {
            expectedMessageCount++;
        }

        Assert.Equal(expectedMessageCount, capturedMessages.Count);

        var messageIndex = 0;
        if (addSystemMessage)
        {
            Assert.Equal(ChatRole.System, capturedMessages[messageIndex].Role);
            Assert.Equal("Test system message", capturedMessages[messageIndex].Text);
            messageIndex++;
        }

        if (addDeveloperMessage)
        {
            Assert.Equal(new ChatRole("developer"), capturedMessages[messageIndex].Role);
            Assert.Equal("Test developer message", capturedMessages[messageIndex].Text);
            messageIndex++;
        }

        // Original user message should be last
        Assert.Equal(ChatRole.User, capturedMessages[messageIndex].Role);
        Assert.Equal("Hello, world!", capturedMessages[messageIndex].Text);
    }

    [Fact]
    public async Task ChatClientExtensionsGetResponseAsyncWithNullSettingsDoesNotCallPrepareChatHistory()
    {
        // Arrange
        var mockChatClient = new Mock<IChatClient>();
        var capturedMessages = new List<ChatMessage>();

        mockChatClient
            .Setup(x => x.GetResponseAsync(It.IsAny<IEnumerable<ChatMessage>>(), It.IsAny<ChatOptions>(), It.IsAny<CancellationToken>()))
            .Callback<IEnumerable<ChatMessage>, ChatOptions?, CancellationToken>((messages, options, ct) =>
            {
                capturedMessages.AddRange(messages);
            })
            .ReturnsAsync(new ChatResponse([new ChatMessage(ChatRole.Assistant, "Test response")]));

        var prompt = "Hello, world!";

        // Act
        await mockChatClient.Object.GetResponseAsync(prompt, executionSettings: null);

        // Assert
        Assert.Single(capturedMessages);
        Assert.Equal(ChatRole.User, capturedMessages[0].Role);
        Assert.Equal("Hello, world!", capturedMessages[0].Text);
    }

    [Fact]
    public async Task ChatClientExtensionsGetStreamingResponseAsyncWithNullSettingsDoesNotCallPrepareChatHistory()
    {
        // Arrange
        var mockChatClient = new Mock<IChatClient>();
        var capturedMessages = new List<ChatMessage>();

        mockChatClient
            .Setup(x => x.GetStreamingResponseAsync(It.IsAny<IEnumerable<ChatMessage>>(), It.IsAny<ChatOptions>(), It.IsAny<CancellationToken>()))
            .Callback<IEnumerable<ChatMessage>, ChatOptions?, CancellationToken>((messages, options, ct) =>
            {
                capturedMessages.AddRange(messages);
            })
            .Returns(new[] { new ChatResponseUpdate(ChatRole.Assistant, "Test streaming response") }.ToAsyncEnumerable());

        var prompt = "Hello, world!";

        // Act
        var responses = new List<ChatResponseUpdate>();
        await foreach (var response in mockChatClient.Object.GetStreamingResponseAsync(prompt, executionSettings: null))
        {
            responses.Add(response);
        }

        // Assert
        Assert.Single(responses);
        Assert.Single(capturedMessages);
        Assert.Equal(ChatRole.User, capturedMessages[0].Role);
        Assert.Equal("Hello, world!", capturedMessages[0].Text);
    }

    /// <summary>
    /// Test implementation of PromptExecutionSettings that overrides PrepareChatHistoryForRequest.
    /// </summary>
    private sealed class TestPromptExecutionSettings : PromptExecutionSettings
    {
        private readonly bool _addSystemMessage;
        private readonly bool _addDeveloperMessage;

        public bool PrepareChatHistoryWasCalled { get; private set; }

        public TestPromptExecutionSettings(bool addSystemMessage, bool addDeveloperMessage)
        {
            this._addSystemMessage = addSystemMessage;
            this._addDeveloperMessage = addDeveloperMessage;
        }

        protected override ChatHistory PrepareChatHistoryForRequest(ChatHistory chatHistory)
        {
            this.PrepareChatHistoryWasCalled = true;

            if (this._addDeveloperMessage)
            {
                chatHistory.Insert(0, new ChatMessageContent(AuthorRole.Developer, "Test developer message"));
            }

            if (this._addSystemMessage)
            {
                chatHistory.Insert(0, new ChatMessageContent(AuthorRole.System, "Test system message"));
            }

            return chatHistory;
        }
    }
}
