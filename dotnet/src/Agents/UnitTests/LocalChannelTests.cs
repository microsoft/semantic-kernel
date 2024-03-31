// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

public class LocalChannelTests
{
    [Fact]
    public async Task VerifyLocalChannelAgentTypeAsync()
    {
        TestAgent agent = new();
        TestChannel channel = new(); // Not a local agent
        await Assert.ThrowsAsync<AgentException>(async () => await channel.InvokeAsync(agent).ToArrayAsync().AsTask());
    }

    private sealed class TestChannel : LocalChannel
    {
        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(Agent agent, CancellationToken cancellationToken = default)
            => base.InvokeAsync(agent, new ChatMessageContent(AuthorRole.User, "hi"), cancellationToken);
    }

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
