// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Unit testing of <see cref="AgentChat"/>.
/// </summary>
public class AgentChatTests
{
    /// <summary>
    /// Verify behavior of <see cref="AgentChat"/> over the course of agent interactions.
    /// </summary>
    [Fact]
    public async Task VerifyAgentChatLifecycleAsync()
    {
        // Create chat
        TestChat chat = new();

        // Verify initial state
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync(chat.Agent)); // Agent history

        // Inject history
        chat.AddChatMessages([new ChatMessageContent(AuthorRole.User, "More")]);
        chat.AddChatMessages([new ChatMessageContent(AuthorRole.User, "And then some")]);

        // Verify updated history
        await this.VerifyHistoryAsync(expectedCount: 2, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync(chat.Agent)); // Agent hasn't joined

        // Invoke with input & verify (agent joins chat)
        chat.AddUserMessage("hi");
        await chat.InvokeAsync().ToArrayAsync();
        Assert.Equal(1, chat.Agent.InvokeCount);

        // Verify updated history
        await this.VerifyHistoryAsync(expectedCount: 4, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 4, chat.GetChatMessagesAsync(chat.Agent)); // Agent history

        // Invoke without input & verify
        await chat.InvokeAsync().ToArrayAsync();
        Assert.Equal(2, chat.Agent.InvokeCount);

        // Verify final history
        await this.VerifyHistoryAsync(expectedCount: 5, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 5, chat.GetChatMessagesAsync(chat.Agent)); // Agent history
    }

    private async Task VerifyHistoryAsync(int expectedCount, IAsyncEnumerable<ChatMessageContent> history)
    {
        if (expectedCount == 0)
        {
            Assert.Empty(history);
        }
        else
        {
            Assert.NotEmpty(history);
            Assert.Equal(expectedCount, await history.CountAsync());
        }
    }

    private sealed class TestChat : AgentChat
    {
        public TestAgent Agent { get; } = new TestAgent();

        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            CancellationToken cancellationToken = default) =>
                this.InvokeAgentAsync(this.Agent, cancellationToken);
    }

    private sealed class TestAgent()
        : ChatHistoryKernelAgent(Kernel.CreateBuilder().Build())
    {
        public override string? Description { get; } = null;

        public override string Id => Guid.NewGuid().ToString();

        public override string? Name { get; } = null;

        public int InvokeCount { get; private set; }

        public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(IReadOnlyList<ChatMessageContent> history, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await Task.Delay(0, cancellationToken);

            this.InvokeCount += 1;

            yield return new ChatMessageContent(AuthorRole.Assistant, "sup");
        }
    }
}
