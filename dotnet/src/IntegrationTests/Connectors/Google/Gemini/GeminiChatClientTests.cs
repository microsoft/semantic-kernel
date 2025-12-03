// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Google.Gemini;

public sealed class GeminiChatClientTests(ITestOutputHelper output) : TestsBase(output)
{
    [RetryTheory]
    [InlineData(false, Skip = "This test is for manual verification.")]
    [InlineData(true, Skip = "This test is for manual verification.")]
    public async Task ChatClientGenerationReturnsValidResponseAsync(bool isVertexAI)
    {
        // Arrange
        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, I'm Brandon, how are you?"),
            new ChatMessage(ChatRole.Assistant, "I'm doing well, thanks for asking."),
            new ChatMessage(ChatRole.User, "Call me by my name and expand this abbreviation: LLM")
        };

        var sut = this.GetChatClient(isVertexAI);

        // Act
        var response = await sut.GetResponseAsync(chatHistory);

        // Assert
        Assert.NotNull(response);
        Assert.NotNull(response.Messages);
        Assert.NotEmpty(response.Messages);
        var content = string.Join("", response.Messages.Select(m => m.Text));
        this.Output.WriteLine(content);
        Assert.Contains("Large Language Model", content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Brandon", content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(false, Skip = "This test is for manual verification.")]
    [InlineData(true, Skip = "This test is for manual verification.")]
    public async Task ChatClientStreamingReturnsValidResponseAsync(bool isVertexAI)
    {
        // Arrange
        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, I'm Brandon, how are you?"),
            new ChatMessage(ChatRole.Assistant, "I'm doing well, thanks for asking."),
            new ChatMessage(ChatRole.User, "Call me by my name and write a long story about my name.")
        };

        var sut = this.GetChatClient(isVertexAI);

        // Act
        var responses = await sut.GetStreamingResponseAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(responses);
        Assert.True(responses.Count > 1);
        var message = string.Concat(responses.Select(c => c.Text));
        Assert.False(string.IsNullOrWhiteSpace(message));
        this.Output.WriteLine(message);
    }

    [RetryTheory]
    [InlineData(false, Skip = "This test is for manual verification.")]
    [InlineData(true, Skip = "This test is for manual verification.")]
    public async Task ChatClientWithSystemMessagesAsync(bool isVertexAI)
    {
        // Arrange
        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.System, "You are helpful assistant. Your name is Roger."),
            new ChatMessage(ChatRole.System, "You know ACDD equals 1520"),
            new ChatMessage(ChatRole.User, "Hello, I'm Brandon, how are you?"),
            new ChatMessage(ChatRole.Assistant, "I'm doing well, thanks for asking."),
            new ChatMessage(ChatRole.User, "Tell me your name and the value of ACDD.")
        };

        var sut = this.GetChatClient(isVertexAI);

        // Act
        var response = await sut.GetResponseAsync(chatHistory);

        // Assert
        Assert.NotNull(response);
        Assert.NotNull(response.Messages);
        Assert.NotEmpty(response.Messages);
        var content = string.Join("", response.Messages.Select(m => m.Text));
        this.Output.WriteLine(content);
        Assert.Contains("1520", content, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Roger", content, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(false, Skip = "This test is for manual verification.")]
    [InlineData(true, Skip = "This test is for manual verification.")]
    public async Task ChatClientStreamingWithSystemMessagesAsync(bool isVertexAI)
    {
        // Arrange
        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.System, "You are helpful assistant. Your name is Roger."),
            new ChatMessage(ChatRole.System, "You know ACDD equals 1520"),
            new ChatMessage(ChatRole.User, "Hello, I'm Brandon, how are you?"),
            new ChatMessage(ChatRole.Assistant, "I'm doing well, thanks for asking."),
            new ChatMessage(ChatRole.User, "Tell me your name and the value of ACDD.")
        };

        var sut = this.GetChatClient(isVertexAI);

        // Act
        var responses = await sut.GetStreamingResponseAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(responses);
        Assert.True(responses.Count > 1);
        var message = string.Concat(responses.Select(c => c.Text));
        this.Output.WriteLine(message);
        Assert.Contains("1520", message, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Roger", message, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(false, Skip = "This test is for manual verification.")]
    [InlineData(true, Skip = "This test is for manual verification.")]
    public async Task ChatClientReturnsUsageDetailsAsync(bool isVertexAI)
    {
        // Arrange
        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, I'm Brandon, how are you?"),
            new ChatMessage(ChatRole.Assistant, "I'm doing well, thanks for asking."),
            new ChatMessage(ChatRole.User, "Call me by my name and expand this abbreviation: LLM")
        };

        var sut = this.GetChatClient(isVertexAI);

        // Act
        var response = await sut.GetResponseAsync(chatHistory);

        // Assert
        Assert.NotNull(response);
        Assert.NotNull(response.Usage);
        this.Output.WriteLine($"Input tokens: {response.Usage.InputTokenCount}");
        this.Output.WriteLine($"Output tokens: {response.Usage.OutputTokenCount}");
        this.Output.WriteLine($"Total tokens: {response.Usage.TotalTokenCount}");
    }

    [RetryTheory]
    [InlineData(false, Skip = "This test is for manual verification.")]
    [InlineData(true, Skip = "This test is for manual verification.")]
    public async Task ChatClientWithChatOptionsAsync(bool isVertexAI)
    {
        // Arrange
        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Generate a random number between 1 and 100.")
        };

        var chatOptions = new ChatOptions
        {
            Temperature = 0.0f,
            MaxOutputTokens = 100
        };

        var sut = this.GetChatClient(isVertexAI);

        // Act
        var response = await sut.GetResponseAsync(chatHistory, chatOptions);

        // Assert
        Assert.NotNull(response);
        Assert.NotNull(response.Messages);
        Assert.NotEmpty(response.Messages);
        var content = string.Join("", response.Messages.Select(m => m.Text));
        this.Output.WriteLine(content);
    }
}
