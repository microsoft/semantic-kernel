// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Unit testing of <see cref="ChatHistoryChannel"/>.
/// </summary>
public class ChatHistoryChannelTests
{
    /// <summary>
    /// Verify a <see cref="ChatHistoryChannel"/> throws if passed an agent that
    /// does not implement <see cref="ChatHistoryAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentIsChatHistoryAgentAsync()
    {
        // Arrange
        Mock<Agent> agent = new(); // Not a ChatHistoryAgent
        ChatHistoryChannel channel = new();

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(() => channel.InvokeAsync(agent.Object).ToArrayAsync().AsTask());
    }

    /// <summary>
    /// Verify a <see cref="ChatHistoryChannel"/> filters empty content on receive.
    /// </summary>
    [Fact]
    public async Task VerifyReceiveFiltersEmptyContentAsync()
    {
        // Arrange
        ChatHistoryChannel channel = new();

        // Act
        await channel.ReceiveAsync([new ChatMessageContent(AuthorRole.Assistant, string.Empty)]);

        // Assert
        Assert.Empty(await channel.GetHistoryAsync().ToArrayAsync());
    }

    /// <summary>
    /// Verify a <see cref="ChatHistoryChannel"/> filters file content on receive.
    /// </summary>
    /// <remarks>
    /// As long as content is not empty, extraneous file content is ok.
    /// </remarks>
    [Fact]
    public async Task VerifyReceiveFiltersFileContentAsync()
    {
        // Arrange
        ChatHistoryChannel channel = new();

        // Act
        await channel.ReceiveAsync([new ChatMessageContent(AuthorRole.Assistant, [new FileReferenceContent("fileId")])]);

        // Assert
        Assert.Empty(await channel.GetHistoryAsync().ToArrayAsync());

        // Act
        await channel.ReceiveAsync(
            [new ChatMessageContent(
                AuthorRole.Assistant,
                [
                    new TextContent("test"),
                    new FileReferenceContent("fileId")
                ])]);

        // Assert
        var history = await channel.GetHistoryAsync().ToArrayAsync();
        Assert.Single(history);
        Assert.Equal(2, history[0].Items.Count);
    }

    /// <summary>
    /// Verify a <see cref="ChatHistoryChannel"/> accepts function content on receive.
    /// </summary>
    [Fact]
    public async Task VerifyReceiveAcceptsFunctionContentAsync()
    {
        // Arrange
        ChatHistoryChannel channel = new();

        // Act
        await channel.ReceiveAsync([new ChatMessageContent(AuthorRole.Assistant, [new FunctionCallContent("test-func")])]);

        // Assert
        Assert.Single(await channel.GetHistoryAsync().ToArrayAsync());

        // Arrange
        channel = new();

        // Act
        await channel.ReceiveAsync([new ChatMessageContent(AuthorRole.Assistant, [new FunctionResultContent("test-func")])]);

        // Assert
        Assert.Single(await channel.GetHistoryAsync().ToArrayAsync());
    }

    /// <summary>
    /// Verify a <see cref="ChatHistoryChannel"/> accepts image content on receive.
    /// </summary>
    [Fact]
    public async Task VerifyReceiveAcceptsImageContentAsync()
    {
        // Arrange
        ChatHistoryChannel channel = new();

        // Act
        await channel.ReceiveAsync([new ChatMessageContent(AuthorRole.Assistant, [new ImageContent(new Uri("http://test.ms/test.jpg"))])]);

        // Assert
        Assert.Single(await channel.GetHistoryAsync().ToArrayAsync());
    }
}
