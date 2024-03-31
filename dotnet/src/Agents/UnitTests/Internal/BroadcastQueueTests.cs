// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Internal;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Internal;

public class BroadcastQueueTests
{
    [Fact]
    public async Task VerifyAsync()
    {
        BroadcastQueue queue = new();

        var isReceiving = await queue.IsRecievingAsync("test");
        Assert.False(isReceiving);

        queue.Enqueue(Array.Empty<ChannelReference>(), Array.Empty<ChatMessageContent>());

        isReceiving = await queue.IsRecievingAsync("test");
        Assert.False(isReceiving);
    }

    // TEST W/ MULTIPLE TASKS ENQUEUE

    // $$$ SPECIAL CHANNEL W/ COUNTS
}
