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

public class BroadcastQueueTests
{
    [Fact]
    public void VerifyBroadcastQueueDefaultConfiguration()
    {
        BroadcastQueue queue = new();

        Assert.True(queue.BlockDuration.TotalSeconds > 0);
    }

    [Fact]
    public async Task VerifyBroadcastQueueReceiveAsync()
    {
        TestChannel channel = new();
        BroadcastQueue queue =
            new()
            {
                BlockDuration = TimeSpan.FromSeconds(0.08),
            };

        ChannelReference reference = new(channel, "test");

        await VerifyReceivingStateAsync(receiveCount: 0, queue, channel, "test");
        Assert.Empty(channel.ReceivedMessages);

        queue.Enqueue(Array.Empty<ChannelReference>(), Array.Empty<ChatMessageContent>());
        await VerifyReceivingStateAsync(receiveCount: 0, queue, channel, "test");
        Assert.Empty(channel.ReceivedMessages);

        queue.Enqueue([reference], Array.Empty<ChatMessageContent>());
        await VerifyReceivingStateAsync(receiveCount: 1, queue, channel, "test");
        Assert.Empty(channel.ReceivedMessages);

        queue.Enqueue([reference], [new ChatMessageContent(AuthorRole.User, "hi")]);
        await VerifyReceivingStateAsync(receiveCount: 2, queue, channel, "test");
        Assert.NotEmpty(channel.ReceivedMessages);

        await queue.FlushAsync();
    }

    [Fact]
    public async Task VerifyBroadcastQueueConcurrencyAsync()
    {
        TestChannel channel = new();
        BroadcastQueue queue =
            new()
            {
                BlockDuration = TimeSpan.FromSeconds(0.08),
            };

        ChannelReference reference = new(channel, "test");

        await BroadcastQueueTests.VerifyReceivingStateAsync(receiveCount: 0, queue, channel, "test");
        Assert.Empty(channel.ReceivedMessages);

        object syncObject = new();

        for (int count = 0; count < 10; ++count)
        {
            queue.Enqueue([new(channel, $"test{count}")], [new ChatMessageContent(AuthorRole.User, "hi")]);
        }

        await queue.FlushAsync();

        for (int count = 0; count < 10; ++count)
        {
            await queue.IsRecievingAsync($"test{count}");
        }

        Assert.NotEmpty(channel.ReceivedMessages);
        Assert.Equal(10, channel.ReceivedMessages.Count);
    }

    private static async Task VerifyReceivingStateAsync(int receiveCount, BroadcastQueue queue, TestChannel channel, string hash)
    {
        bool isReceiving = await queue.IsRecievingAsync(hash);
        Assert.False(isReceiving);
        Assert.Equal(receiveCount, channel.ReceiveCount);
    }

    // TEST W/ MULTIPLE TASKS ENQUEUE

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
