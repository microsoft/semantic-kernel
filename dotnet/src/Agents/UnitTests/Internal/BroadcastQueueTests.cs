// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
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
        BroadcastQueue queue = new();

        Assert.True(queue.BlockDuration.TotalSeconds > 0);
    }

    /// <summary>
    /// Verify behavior of <see cref="BroadcastQueue"/> over the course of multiple interactions.
    /// </summary>
    [Fact]
    public async Task VerifyBroadcastQueueReceiveAsync()
    {
        // Create nexus and channel.
        BroadcastQueue queue =
            new()
            {
                BlockDuration = TimeSpan.FromSeconds(0.08),
            };
        TestChannel channel = new();
        ChannelReference reference = new(channel, "test");

        // Verify initial state
        await VerifyReceivingStateAsync(receiveCount: 0, queue, channel, "test");
        Assert.Empty(channel.ReceivedMessages);

        // Verify empty invocation with no channels.
        queue.Enqueue(Array.Empty<ChannelReference>(), Array.Empty<ChatMessageContent>());
        await VerifyReceivingStateAsync(receiveCount: 0, queue, channel, "test");
        Assert.Empty(channel.ReceivedMessages);

        // Verify empty invocation of channel.
        queue.Enqueue([reference], Array.Empty<ChatMessageContent>());
        await VerifyReceivingStateAsync(receiveCount: 1, queue, channel, "test");
        Assert.Empty(channel.ReceivedMessages);

        // Verify expected invocation of channel.
        queue.Enqueue([reference], [new ChatMessageContent(AuthorRole.User, "hi")]);
        await VerifyReceivingStateAsync(receiveCount: 2, queue, channel, "test");
        Assert.NotEmpty(channel.ReceivedMessages);

        await queue.FlushAsync();
    }

    /// <summary>
    /// Verify behavior of <see cref="BroadcastQueue"/> with queuing of multiple channels.
    /// </summary>
    [Fact]
    public async Task VerifyBroadcastQueueConcurrencyAsync()
    {
        // Create nexus and channel.
        BroadcastQueue queue =
            new()
            {
                BlockDuration = TimeSpan.FromSeconds(0.08),
            };
        TestChannel channel = new();
        ChannelReference reference = new(channel, "test");

        // Enqueue multiple channels
        object syncObject = new();

        for (int count = 0; count < 10; ++count)
        {
            queue.Enqueue([new(channel, $"test{count}")], [new ChatMessageContent(AuthorRole.User, "hi")]);
        }

        // Drain all queues.
        for (int count = 0; count < 10; ++count)
        {
            await queue.IsReceivingAsync($"test{count}");
        }

        // Verify result
        Assert.NotEmpty(channel.ReceivedMessages);
        Assert.Equal(10, channel.ReceivedMessages.Count);
    }

    private static async Task VerifyReceivingStateAsync(int receiveCount, BroadcastQueue queue, TestChannel channel, string hash)
    {
        bool isReceiving = await queue.IsReceivingAsync(hash);
        Assert.False(isReceiving);
        Assert.Equal(receiveCount, channel.ReceiveCount);
    }

    private sealed class TestChannel : AgentChannel
    {
        public TimeSpan ReceiveDuration { get; set; } = TimeSpan.FromSeconds(0.3);

        public int ReceiveCount { get; private set; }

        public List<ChatMessageContent> ReceivedMessages { get; } = new();

        protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }

        protected internal override IAsyncEnumerable<ChatMessageContent> InvokeAsync(Agent agent, ChatMessageContent? input = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        protected internal override async Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            this.ReceivedMessages.AddRange(history);
            this.ReceiveCount += 1;

            await Task.Delay(this.ReceiveDuration, cancellationToken);
        }
    }
}
