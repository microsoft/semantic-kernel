// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Google.Gemini;

public sealed class GeminiGenAIChatClientTests(ITestOutputHelper output) : TestsBase(output)
{
    private const string SkipReason = "This test is for manual verification.";

    [RetryFact(Skip = SkipReason)]
    public async Task ChatClientGenerationReturnsValidResponseAsync()
    {
        // Arrange
        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, I'm Brandon, how are you?"),
            new ChatMessage(ChatRole.Assistant, "I'm doing well, thanks for asking."),
            new ChatMessage(ChatRole.User, "Call me by my name and expand this abbreviation: LLM")
        };

        var sut = this.GetGenAIChatClient();

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

    [RetryFact(Skip = SkipReason)]
    public async Task ChatClientStreamingReturnsValidResponseAsync()
    {
        // Arrange
        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, I'm Brandon, how are you?"),
            new ChatMessage(ChatRole.Assistant, "I'm doing well, thanks for asking."),
            new ChatMessage(ChatRole.User, "Call me by my name and write a long story about my name.")
        };

        var sut = this.GetGenAIChatClient();

        // Act
        var responses = await sut.GetStreamingResponseAsync(chatHistory).ToListAsync();

        // Assert
        Assert.NotEmpty(responses);
        Assert.True(responses.Count > 1);
        var message = string.Concat(responses.Select(c => c.Text));
        Assert.False(string.IsNullOrWhiteSpace(message));
        this.Output.WriteLine(message);
    }

    [RetryFact(Skip = SkipReason)]
    public async Task ChatClientWithSystemMessagesAsync()
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

        var sut = this.GetGenAIChatClient();

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

    [RetryFact(Skip = SkipReason)]
    public async Task ChatClientStreamingWithSystemMessagesAsync()
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

        var sut = this.GetGenAIChatClient();

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

    [RetryFact(Skip = SkipReason)]
    public async Task ChatClientReturnsUsageDetailsAsync()
    {
        // Arrange
        var chatHistory = new[]
        {
            new ChatMessage(ChatRole.User, "Hello, I'm Brandon, how are you?"),
            new ChatMessage(ChatRole.Assistant, "I'm doing well, thanks for asking."),
            new ChatMessage(ChatRole.User, "Call me by my name and expand this abbreviation: LLM")
        };

        var sut = this.GetGenAIChatClient();

        // Act
        var response = await sut.GetResponseAsync(chatHistory);

        // Assert
        Assert.NotNull(response);
        Assert.NotNull(response.Usage);
        this.Output.WriteLine($"Input tokens: {response.Usage.InputTokenCount}");
        this.Output.WriteLine($"Output tokens: {response.Usage.OutputTokenCount}");
        this.Output.WriteLine($"Total tokens: {response.Usage.TotalTokenCount}");
    }

    [RetryFact(Skip = SkipReason)]
    public async Task ChatClientWithChatOptionsAsync()
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

        var sut = this.GetGenAIChatClient();

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
