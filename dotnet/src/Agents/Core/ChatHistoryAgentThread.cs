// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents a conversation thread based on an instance of <see cref="ChatHistory"/> that is maanged inside this class.
/// </summary>
public sealed class ChatHistoryAgentThread : AgentThread
{
    private readonly ChatHistory _chatHistory = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryAgentThread"/> class.
    /// </summary>
    public ChatHistoryAgentThread()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryAgentThread"/> class that resumes an existing thread.
    /// </summary>
    /// <param name="chatHistory">An existing chat history to base this thread on.</param>
    /// <param name="id">The id of the existing thread. If not provided, a new one will be generated.</param>
    public ChatHistoryAgentThread(ChatHistory chatHistory, string? id = null)
    {
        Verify.NotNull(chatHistory);
        this._chatHistory = chatHistory;
        this.Id = id ?? Guid.NewGuid().ToString("N");
    }

    /// <inheritdoc />
    protected override Task<string?> CreateInternalAsync(CancellationToken cancellationToken)
    {
        return Task.FromResult<string?>(Guid.NewGuid().ToString("N"));
    }

    /// <inheritdoc />
    protected override Task DeleteInternalAsync(CancellationToken cancellationToken)
    {
        this._chatHistory.Clear();
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    protected override Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        this._chatHistory.Add(newMessage);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    [Experimental("SKEXP0110")]
    public async IAsyncEnumerable<ChatMessageContent> GetMessagesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (this.IsDeleted)
        {
            throw new InvalidOperationException("This thread has been deleted and cannot be used anymore.");
        }

        if (this.Id is null)
        {
            await this.CreateAsync(cancellationToken).ConfigureAwait(false);
        }

        foreach (var message in this._chatHistory)
        {
            yield return message;
        }
    }
}
