// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using Microsoft.SemanticKernel.Agents.Filters;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using Microsoft.SemanticKernel.Agents.Filters;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using Microsoft.SemanticKernel.Agents.Filters;
>>>>>>> main
>>>>>>> Stashed changes
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

        // Inject history
        chat.Add([new ChatMessageContent(AuthorRole.User, "More")]);
        chat.Add([new ChatMessageContent(AuthorRole.User, "And then some")]);
        // Act: Inject history
        chat.AddChatMessages([new ChatMessageContent(AuthorRole.User, "More")]);
        chat.AddChatMessages([new ChatMessageContent(AuthorRole.User, "And then some")]);

        // Assert: Verify updated history
        await this.VerifyHistoryAsync(expectedCount: 2, chat.GetChatMessagesAsync()); // Primary history
        await this.VerifyHistoryAsync(expectedCount: 0, chat.GetChatMessagesAsync(chat.Agent)); // Agent hasn't joined

        // Invoke with input & verify (agent joins chat)
        chat.Add(new ChatMessageContent(AuthorRole.User, "hi"));
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// <summary>
    /// Verify behavior of <see cref="AgentChat"/> over the course of agent interactions.
    /// </summary>
    [Fact]
    public void VerifyAgentChatRejectsSystemMessage()
    {
        // Create chat
        TestChat chat = new();

        // Add a system message
        Assert.Throws<KernelException>(() => chat.AddChatMessage(new ChatMessageContent(AuthorRole.System, "hi")));
    /// Verify behavior of <see cref="AgentChat"/> usage of <see cref="IAgentChatFilter"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentChatFiltersAsync()
    {
        // Create a filter
        Mock<IAgentChatFilter> mockFilter = new();

        // Create chat
        TestChat chat = new()
        {
            Filters =
            {
                mockFilter.Object
            }
        };

        // Verify initial state
        mockFilter.Verify(f => f.OnAgentInvoking(It.IsAny<AgentChatFilterInvokingContext>()), Times.Never);
        mockFilter.Verify(f => f.OnAgentInvoked(It.IsAny<AgentChatFilterInvokedContext>()), Times.Never);

        // Invoke with input & verify (agent joins chat)
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "hi"));
        await chat.InvokeAsync().ToArrayAsync();
        Assert.Equal(1, chat.Agent.InvokeCount);
        mockFilter.Verify(f => f.OnAgentInvoking(It.IsAny<AgentChatFilterInvokingContext>()), Times.Once);
        mockFilter.Verify(f => f.OnAgentInvoked(It.IsAny<AgentChatFilterInvokedContext>()), Times.Once);
    }

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    private async Task VerifyHistoryAsync(int expectedCount, IAsyncEnumerable<ChatMessageContent> history)
    {
        Assert.Equal(expectedCount, await history.CountAsync());
    }

    private sealed class TestChat : AgentChat
    {
        public MockAgent Agent { get; } = new() { Response = [new(AuthorRole.Assistant, "sup")] };

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
        public override IReadOnlyList<Agent> Agents => [this.Agent];

>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        public override IReadOnlyList<Agent> Agents => [this.Agent];

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            CancellationToken cancellationToken = default) =>
                this.InvokeAgentAsync(this.Agent, cancellationToken);

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        public IAsyncEnumerable<ChatMessageContent> InvalidInvokeAsync(
            CancellationToken cancellationToken = default)
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        public IAsyncEnumerable<ChatMessageContent> InvalidInvokeAsync(
            CancellationToken cancellationToken = default)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        public IAsyncEnumerable<ChatMessageContent> InvalidInvokeAsync(
            CancellationToken cancellationToken = default)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            ChatHistory history,
            IReadOnlyList<ChatMessageContent> history,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> origin/PR
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
>>>>>>> origin/PR
=======
        public IAsyncEnumerable<ChatMessageContent> InvalidInvokeAsync(
            CancellationToken cancellationToken = default)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        public IAsyncEnumerable<ChatMessageContent> InvalidInvokeAsync(
            CancellationToken cancellationToken = default)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
