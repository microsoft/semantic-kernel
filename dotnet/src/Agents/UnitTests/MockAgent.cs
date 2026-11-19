// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
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

    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.InvokeCount++;

        if (thread == null)
        {
            Mock<AgentThread> mockThread = new();
            thread = mockThread.Object;
        }

        foreach (ChatMessageContent response in this.Response)
        {
            AgentResponseItem<ChatMessageContent> responseItem = new(response, thread);
            if (options?.OnIntermediateMessage is not null)
            {
                await options.OnIntermediateMessage(responseItem);
                yield return responseItem;
            }
        }
    }

    protected internal override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this.InvokeCount++;

        return this.Response.ToAsyncEnumerable();
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.InvokeCount++;

        if (thread == null)
        {
            Mock<AgentThread> mockThread = new();
            thread = mockThread.Object;
        }

        foreach (ChatMessageContent response in this.Response)
        {
            if (options?.OnIntermediateMessage is not null)
            {
                await options.OnIntermediateMessage(new AgentResponseItem<ChatMessageContent>(response, thread));
                yield return new AgentResponseItem<StreamingChatMessageContent>(new StreamingChatMessageContent(response.Role, response.Content), thread);
            }
        }
    }

    protected internal override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this.InvokeCount++;
        return this.Response.Select(m => new StreamingChatMessageContent(m.Role, m.Content)).ToAsyncEnumerable();
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
