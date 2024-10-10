// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents;
using Moq;
using Xunit;

namespace SemanticKernel.Experimental.Agents.UnitTests;
public class ChatCompletionAgentTests
{
    private readonly IKernelBuilder _kernelBuilder;

    private readonly Mock<IChatCompletionService> _mockChatCompletionService;

    public ChatCompletionAgentTests()
    {
        this._kernelBuilder = Kernel.CreateBuilder();

        this._mockChatCompletionService = new Mock<IChatCompletionService>();

        this._kernelBuilder.Services.AddSingleton<IChatCompletionService>(this._mockChatCompletionService.Object);
    }

    [Fact]
    public async Task ItShouldResolveChatCompletionServiceFromKernelAsync()
    {
        // Arrange
        this._mockChatCompletionService
           .Setup(ccs => ccs.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
           .ReturnsAsync(new List<ChatMessageContent>());

        var agent = new ChatCompletionAgent(this._kernelBuilder.Build(), "fake-name", "fake-instructions", "fake-description");

        // Act
        var result = await agent.InvokeAsync(new List<ChatMessageContent>());

        // Assert
        this._mockChatCompletionService.Verify(x =>
        x.GetChatMessageContentsAsync(
            It.IsAny<ChatHistory>(),
            It.IsAny<PromptExecutionSettings>(),
            It.IsAny<Kernel>(),
            It.IsAny<CancellationToken>()),
        Times.Once);
    }

    [Fact]
    public async Task ItShouldAddSystemInstructionsAndMessagesToChatHistoryAsync()
    {
        // Arrange
        this._mockChatCompletionService
           .Setup(ccs => ccs.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
           .ReturnsAsync(new List<ChatMessageContent>());

        var agent = new ChatCompletionAgent(this._kernelBuilder.Build(), "name", "fake-instructions", "fake-description");

        // Act
        var result = await agent.InvokeAsync(new List<ChatMessageContent>() { new(AuthorRole.User, "fake-user-message") });

        // Assert
        this._mockChatCompletionService.Verify(
            x => x.GetChatMessageContentsAsync(
                It.Is<ChatHistory>(ch => ch.Count == 2 &&
                                         ch.Any(m => m.Role == AuthorRole.System && m.Content == "fake-instructions") &&
                                         ch.Any(m => m.Role == AuthorRole.User && m.Items!.OfType<TextContent>().Any(c => c.Text == "fake-user-message"))),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task ItShouldReturnChatCompletionServiceMessagesAsync()
    {
        // Arrange
        this._mockChatCompletionService
            .Setup(ccs => ccs.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<ChatMessageContent> {
                new(AuthorRole.Assistant, "fake-assistant-message-1"),
                new(AuthorRole.Assistant, "fake-assistant-message-2")
            });

        var agent = new ChatCompletionAgent(this._kernelBuilder.Build(), "name", "fake-instructions", "fake-description");

        // Act
        var result = await agent.InvokeAsync(new List<ChatMessageContent>());

        // Assert
        Assert.Equal(2, result.Count);
        Assert.Contains(result, m => m.Role == AuthorRole.Assistant && (m.Items?.OfType<TextContent>().Any(c => c.Text == "fake-assistant-message-1") ?? false));
        Assert.Contains(result, m => m.Role == AuthorRole.Assistant && (m.Items?.OfType<TextContent>().Any(c => c.Text == "fake-assistant-message-2") ?? false));
    }
}
