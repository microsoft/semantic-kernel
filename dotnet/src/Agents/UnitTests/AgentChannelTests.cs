// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Unit testing of <see cref="AgentChannel"/>.
/// </summary>
public class AgentChannelTests
{
    /// <summary>
    /// Verify a <see cref="AgentChannel{TAgent}"/> throws if passed
    /// an agent type that does not match declared agent type (TAgent).
    /// </summary>
    [Fact]
    public async Task VerifyAgentChannelUpcastAsync()
    {
        TestChannel channel = new();
        Assert.Equal(0, channel.InvokeCount);

        var messages = channel.InvokeAgentAsync(new TestAgent()).ToArrayAsync();
        Assert.Equal(1, channel.InvokeCount);

        await Assert.ThrowsAsync<KernelException>(() => channel.InvokeAgentAsync(new NextAgent()).ToArrayAsync().AsTask());
        Assert.Equal(1, channel.InvokeCount);
    }

    /// <summary>
    /// Not using mock as the goal here is to provide entrypoint to protected method.
    /// </summary>
    private sealed class TestChannel : AgentChannel<TestAgent>
    {
        public int InvokeCount { get; private set; }

        public IAsyncEnumerable<ChatMessageContent> InvokeAgentAsync(Agent agent, CancellationToken cancellationToken = default)
            => base.InvokeAsync(agent, cancellationToken);

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        protected internal override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(TestAgent agent, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
        {
            this.InvokeCount++;

            yield break;
        }

        protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }

        protected internal override Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }

    private sealed class NextAgent : TestAgent;

    private class TestAgent : KernelAgent
    {
        protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }

        protected internal override IEnumerable<string> GetChannelKeys()
        {
            throw new NotImplementedException();
        }
    }
}
