// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
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
        // Arrange: Create chat
        TestChat chat = new();

        // Assert: Verify initial state
        Assert.False(chat.IsActive);
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync(chat.Agent)); // Agent history

        // Act: Inject history
        chat.AddChatMessages([new ChatMessageContent(AuthorRole.User, "More")]);
        chat.AddChatMessages([new ChatMessageContent(AuthorRole.User, "And then some")]);

        // Assert: Verify updated history
        await this.VerifyHistoryAsync(expectedCount: 2, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync(chat.Agent)); // Agent hasn't joined

        // Act: Invoke with input & verify (agent joins chat)
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "hi"));
        await chat.InvokeAsync().ToArrayAsync();

        // Assert: Verify updated history
        Assert.Equal(1, chat.Agent.InvokeCount);
        await this.VerifyHistoryAsync(expectedCount: 4, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 4, chat.GetChatMessagesAsync(chat.Agent)); // Agent history

        // Act: Invoke without input
        await chat.InvokeAsync().ToArrayAsync();

        // Assert: Verify final history
        Assert.Equal(2, chat.Agent.InvokeCount);
        await this.VerifyHistoryAsync(expectedCount: 5, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 5, chat.GetChatMessagesAsync(chat.Agent)); // Agent history

        // Reset verify
        await chat.ResetAsync();
        Assert.Equal(2, chat.Agent.InvokeCount);

        // Verify final history
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync(chat.Agent)); // Agent history
    }

    /// <summary>
    /// Verify <see cref="AgentChat"/> throw exception for system message.
    /// </summary>
    [Fact]
    public void VerifyAgentChatRejectsSystemMessage()
    {
        // Arrange: Create chat
        TestChat chat = new() { LoggerFactory = new Mock<ILoggerFactory>().Object };

        // Assert and Act: Verify system message not accepted
        Assert.Throws<KernelException>(() => chat.AddChatMessage(new ChatMessageContent(AuthorRole.System, "hi")));
    }

    /// <summary>
    /// Verify <see cref="AgentChat"/> throw exception for if invoked when active.
    /// </summary>
    [Fact]
    public async Task VerifyAgentChatThrowsWhenActiveAsync()
    {
        // Arrange: Create chat
        TestChat chat = new();

        // Assert and Act: Verify system message not accepted
        await Assert.ThrowsAsync<KernelException>(() => chat.InvalidInvokeAsync().ToArrayAsync().AsTask());
    }

    /// <summary>
    /// Verify the management of <see cref="Agent"/> instances as they join <see cref="AgentChat"/>.
    /// </summary>
    [Fact(Skip = "Not 100% reliable for github workflows, but useful for dev testing.")]
    public async Task VerifyGroupAgentChatConcurrencyAsync()
    {
        // Arrange
        TestChat chat = new();

        Task[] tasks;

        int isActive = 0;

        // Act: Queue concurrent tasks
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

        // Assert: Verify failure
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
        Assert.Equal(expectedCount, await history.CountAsync());
    }

    private sealed class TestChat : AgentChat
    {
        public MockAgent Agent { get; } = new() { Response = [new(AuthorRole.Assistant, "sup")] };

        public override IReadOnlyList<Agent> Agents => [this.Agent];

        public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            CancellationToken cancellationToken = default) =>
                this.InvokeAgentAsync(this.Agent, cancellationToken);

        public IAsyncEnumerable<ChatMessageContent> InvalidInvokeAsync(
            CancellationToken cancellationToken = default)
        {
            this.SetActivityOrThrow();
            return this.InvokeAgentAsync(this.Agent, cancellationToken);
        }

        public override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(CancellationToken cancellationToken = default)
        {
            StreamingChatMessageContent[] messages = [new StreamingChatMessageContent(AuthorRole.Assistant, "sup")];
            return messages.ToAsyncEnumerable();
        }
    }
}
