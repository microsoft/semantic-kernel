// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
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
        Assert.False(chat.IsActive);
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync(chat.Agent)); // Agent history

        // Inject history
        chat.Add([new ChatMessageContent(AuthorRole.User, "More")]);
        chat.Add([new ChatMessageContent(AuthorRole.User, "And then some")]);

        // Verify updated history
        await this.VerifyHistoryAsync(expectedCount: 2, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync(chat.Agent)); // Agent hasn't joined

        // Invoke with input & verify (agent joins chat)
        chat.Add(new ChatMessageContent(AuthorRole.User, "hi"));
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

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact(Skip = "Not 100% reliable for github workflows, but useful for dev testing.")]
    public async Task VerifyGroupAgentChatConcurrencyAsync()
    {
        TestChat chat = new();

        Task[] tasks;

        int isActive = 0;

        // Queue concurrent tasks
        object syncObject = new();
        lock (syncObject)
        {
            tasks =
                [
                    Task.Run(() => SynchronizedInvokeAsync()),
                    Task.Run(() => SynchronizedInvokeAsync()),
                    Task.Run(() => SynchronizedInvokeAsync()),
                    Task.Run(() => SynchronizedInvokeAsync()),
                    Task.Run(() => SynchronizedInvokeAsync()),
                    Task.Run(() => SynchronizedInvokeAsync()),
                    Task.Run(() => SynchronizedInvokeAsync()),
                    Task.Run(() => SynchronizedInvokeAsync()),
                ];
        }

        // Signal tasks to execute
        Interlocked.CompareExchange(ref isActive, 1, 0);

        await Task.Yield();

        // Verify failure
        await Assert.ThrowsAsync<KernelException>(() => Task.WhenAll(tasks));

        async Task SynchronizedInvokeAsync()
        {
            // Loop until signaled
            int isReady;
            do
            {
                isReady = Interlocked.CompareExchange(ref isActive, 1, 1);
            }
            while (isReady == 0);

            // Rush invocation
            await chat.InvokeAsync().ToArrayAsync().AsTask();
        }
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

        public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            CancellationToken cancellationToken = default) =>
                this.InvokeAgentAsync(this.Agent, cancellationToken);
    }

    private sealed class TestAgent : ChatHistoryKernelAgent
    {
        public int InvokeCount { get; private set; }

        public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            IReadOnlyList<ChatMessageContent> history,
            ILogger logger,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await Task.Delay(0, cancellationToken);

            this.InvokeCount++;

            yield return new ChatMessageContent(AuthorRole.Assistant, "sup");
        }
    }
}
