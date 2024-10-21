// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Internal;

/// <summary>
/// Unit testing of <see cref="BroadcastQueue"/>.
/// </summary>
public class BroadcastQueueTests
{
    /// <summary>
    /// Verify the default configuration.
    /// </summary>
    [Fact]
    public void VerifyBroadcastQueueDefaultConfiguration()
    {
        // Arrange
        BroadcastQueue queue = new();

        // Assert
        Assert.True(queue.BlockDuration.TotalSeconds > 0);
    }

    /// <summary>
    /// Verify behavior of <see cref="BroadcastQueue"/> over the course of multiple interactions.
    /// </summary>
    [Fact]
    public async Task VerifyBroadcastQueueReceiveAsync()
    {
        // Arrange: Create queue and channel.
        BroadcastQueue queue =
            new()
            {
                BlockDuration = TimeSpan.FromSeconds(0.08),
            };
        MockChannel channel = new();
        ChannelReference reference = new(channel, "test");

        // Act: Verify initial state
        await VerifyReceivingStateAsync(receiveCount: 0, queue, channel, "test");

        // Assert
        Assert.Empty(channel.ReceivedMessages);

        // Act: Verify empty invocation with no channels.
        queue.Enqueue([], []);
        await VerifyReceivingStateAsync(receiveCount: 0, queue, channel, "test");

        // Assert
        Assert.Empty(channel.ReceivedMessages);

        // Act: Verify empty invocation of channel.
        queue.Enqueue([reference], []);
        await VerifyReceivingStateAsync(receiveCount: 1, queue, channel, "test");

        // Assert
        Assert.Empty(channel.ReceivedMessages);

        // Act: Verify expected invocation of channel.
        queue.Enqueue([reference], [new ChatMessageContent(AuthorRole.User, "hi")]);
        await VerifyReceivingStateAsync(receiveCount: 2, queue, channel, "test");

        // Assert
        Assert.NotEmpty(channel.ReceivedMessages);
    }

    /// <summary>
    /// Verify behavior of <see cref="BroadcastQueue"/> over the course of multiple interactions.
    /// </summary>
    [Fact]
    public async Task VerifyBroadcastQueueFailureAsync()
    {
        // Arrange: Create queue and channel.
        BroadcastQueue queue =
            new()
            {
                BlockDuration = TimeSpan.FromSeconds(0.08),
            };
        MockChannel channel = new() { MockException = new InvalidOperationException("Test") };
        ChannelReference reference = new(channel, "test");

        // Act: Verify expected invocation of channel.
        queue.Enqueue([reference], [new ChatMessageContent(AuthorRole.User, "hi")]);

        // Assert
        await Assert.ThrowsAsync<KernelException>(() => queue.EnsureSynchronizedAsync(reference));
        await Assert.ThrowsAsync<KernelException>(() => queue.EnsureSynchronizedAsync(reference));
        await Assert.ThrowsAsync<KernelException>(() => queue.EnsureSynchronizedAsync(reference));
    }

    /// <summary>
    /// Verify behavior of <see cref="BroadcastQueue"/> with queuing of multiple channels.
    /// </summary>
    [Fact]
    public async Task VerifyBroadcastQueueConcurrencyAsync()
    {
        // Arrange: Create queue and channel.
        BroadcastQueue queue =
            new()
            {
                BlockDuration = TimeSpan.FromSeconds(0.08),
            };
        MockChannel channel = new();
        ChannelReference reference = new(channel, "test");

        // Act: Enqueue multiple channels
        for (int count = 0; count < 10; ++count)
        {
            queue.Enqueue([new(channel, $"test{count}")], [new ChatMessageContent(AuthorRole.User, "hi")]);
        }

        // Drain all queues.
        for (int count = 0; count < 10; ++count)
        {
            await queue.EnsureSynchronizedAsync(new ChannelReference(channel, $"test{count}"));
        }

        // Assert
        Assert.NotEmpty(channel.ReceivedMessages);
        Assert.Equal(10, channel.ReceivedMessages.Count);
    }

    private static async Task VerifyReceivingStateAsync(int receiveCount, BroadcastQueue queue, MockChannel channel, string hash)
    {
        await queue.EnsureSynchronizedAsync(new ChannelReference(channel, hash));
        Assert.Equal(receiveCount, channel.ReceiveCount);
    }

    private sealed class TestChannel : MockChannel
    {
        public int ReceiveCount { get; private set; }

        public List<ChatMessageContent> ReceivedMessages { get; } = [];

        protected internal override async Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            this.ReceivedMessages.AddRange(history);
            this.ReceiveCount++;

            await Task.Delay(this.ReceiveDuration, cancellationToken);
        }
    }

    private sealed class BadChannel : MockChannel
    {
        protected internal override async Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            await Task.Delay(this.ReceiveDuration, cancellationToken);

            throw new InvalidOperationException("Test");
        }
    }

    private abstract class MockChannel : AgentChannel
    {
        public TimeSpan ReceiveDuration { get; set; } = TimeSpan.FromSeconds(0.1);

        protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }

        protected internal override IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(Agent agent, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        protected internal override string Serialize()
        {
            throw new NotImplementedException();
        }
    }
}
