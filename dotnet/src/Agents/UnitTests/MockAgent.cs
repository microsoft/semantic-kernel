// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Mock definition of <see cref="Agent"/> with a <see cref="ChatHistoryAgent"/> contract.
/// </summary>
internal sealed class MockAgent : ChatHistoryAgent
{
    public int InvokeCount { get; private set; }

    public IReadOnlyList<ChatMessageContent> Response { get; set; } = [];

    public override IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        this.InvokeCount++;
        if (thread == null)
        {
            Mock<AgentThread> mockThread = new();
            thread = mockThread.Object;
        }
        return this.Response.Select(x => new AgentResponseItem<ChatMessageContent>(x, thread!)).ToAsyncEnumerable();
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        this.InvokeCount++;
        return this.Response.Select(m => new AgentResponseItem<StreamingChatMessageContent>(new StreamingChatMessageContent(m.Role, m.Content), thread!)).ToAsyncEnumerable();
    }

    protected internal override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        ChatHistory history =
            JsonSerializer.Deserialize<ChatHistory>(channelState) ??
            throw new KernelException("Unable to restore channel: invalid state.");
        return Task.FromResult<AgentChannel>(new ChatHistoryChannel(history));
    }

    // Expose protected method for testing
    public new Task<string?> RenderInstructionsAsync(Kernel kernel, KernelArguments? arguments, CancellationToken cancellationToken)
    {
        return base.RenderInstructionsAsync(kernel, arguments, cancellationToken);
    }
}
