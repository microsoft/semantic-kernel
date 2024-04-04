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

/// <summary>
/// Unit testing of <see cref="ChatHistoryChannel"/>.
/// </summary>
public class ChatHistoryChannelTests
{
    /// <summary>
    /// Verify a <see cref="ChatHistoryChannel"/> throws if passed an agent that
    /// does not implement <see cref="IChatHistoryHandler"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentWithoutIChatHistoryHandlerAsync()
    {
        TestAgent agent = new(); // Not a IChatHistoryHandler
        TestChannel channel = new(); // Requires IChatHistoryHandler
        await Assert.ThrowsAsync<KernelException>(() => channel.InvokeAsync(agent).ToArrayAsync().AsTask());
    }

    private sealed class TestChannel : ChatHistoryChannel
    {
        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(Agent agent, CancellationToken cancellationToken = default)
            => base.InvokeAsync(agent, new ChatMessageContent(AuthorRole.User, "hi"), cancellationToken);
    }

    private sealed class TestAgent()
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
