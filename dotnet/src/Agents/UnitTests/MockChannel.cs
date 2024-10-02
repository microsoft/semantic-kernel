// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace SemanticKernel.Agents.UnitTests;

internal sealed class MockChannel : AgentChannel<MockAgent>
{
    public Exception? MockException { get; set; }

    public int InvokeCount { get; private set; }

    public int ReceiveCount { get; private set; }

    public TimeSpan ReceiveDuration { get; set; } = TimeSpan.FromSeconds(0.3);

    public List<ChatMessageContent> ReceivedMessages { get; } = [];

    protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    public IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAgentAsync(Agent agent, CancellationToken cancellationToken = default)
        => base.InvokeAsync(agent, cancellationToken);

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    protected internal override async IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(MockAgent agent, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
    {
        this.InvokeCount++;

        if (this.MockException is not null)
        {
            throw this.MockException;
        }

        yield break;
    }

    protected internal override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(MockAgent agent, IList<ChatMessageContent> messages, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    protected internal override async Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        this.ReceivedMessages.AddRange(history);
        this.ReceiveCount++;

        await Task.Delay(this.ReceiveDuration, cancellationToken);

        if (this.MockException is not null)
        {
            throw this.MockException;
        }
    }

    protected internal override Task ResetAsync(CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    protected internal override string Serialize()
    {
        throw new NotImplementedException();
    }
}
