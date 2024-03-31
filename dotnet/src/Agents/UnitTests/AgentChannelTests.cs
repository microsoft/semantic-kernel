// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

public class AgentChannelTests
{
    [Fact]
    public async Task VerifyAgentChannelUpcastAsync()
    {
        TestChannel channel = new();
        Assert.Equal(0, channel.InvokeCount);

        var messages = channel.InvokeAgentAsync(new TestAgent()).ToArrayAsync();
        Assert.Equal(1, channel.InvokeCount);

        Assert.Throws<AgentException>(() => messages = channel.InvokeAgentAsync(new NextAgent()).ToArrayAsync());
        Assert.Equal(1, channel.InvokeCount);
    }

    private sealed class TestChannel : AgentChannel<TestAgent>
    {
        public int InvokeCount { get; private set; }

        public IAsyncEnumerable<ChatMessageContent> InvokeAgentAsync(Agent agent, CancellationToken cancellationToken = default)
            => base.InvokeAsync(agent, new ChatMessageContent(AuthorRole.User, "hi"), cancellationToken);

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        protected internal override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(TestAgent agent, ChatMessageContent? input = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
        {
            this.InvokeCount += 1;

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

    private sealed class NextAgent()
        : TestAgent() { }

    private class TestAgent()
        : KernelAgent(Kernel.CreateBuilder().Build())
    {
        public override string? Description { get; } = null;

        public override string Id => Guid.NewGuid().ToString();

        public override string? Name { get; } = null;

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
