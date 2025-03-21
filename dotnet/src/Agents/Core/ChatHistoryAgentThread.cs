// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
    private string? _id = null;
    private bool _isDeleted = false;

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
        this._id = id ?? Guid.NewGuid().ToString("N");
    }

    /// <inheritdoc />
    public override string? Id => this._id;

    /// <inheritdoc/>
    public override Task<string> CreateAsync(CancellationToken cancellationToken = default)
    {
        if (this._isDeleted)
        {
            throw new InvalidOperationException("This thread has been deleted and cannot be recreated.");
        }

        if (this._id is not null)
        {
            return Task.FromResult(this._id);
        }

        this._id = Guid.NewGuid().ToString("N");

        return Task.FromResult(this._id);
    }

    /// <inheritdoc/>
    public override Task DeleteAsync(CancellationToken cancellationToken = default)
    {
        if (this._isDeleted)
        {
            return Task.CompletedTask;
        }

        if (this._id is null)
        {
            throw new InvalidOperationException("This thread cannot be deleted, since it has not been created.");
        }

        this._chatHistory.Clear();
        this._isDeleted = true;

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public async override Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        if (this._isDeleted)
        {
            throw new InvalidOperationException("This thread has been deleted and cannot be used anymore.");
        }

        if (this._id is null)
        {
            await this.CreateAsync(cancellationToken).ConfigureAwait(false);
        }

        this._chatHistory.Add(newMessage);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<ChatMessageContent> GetMessagesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (this._isDeleted)
        {
            throw new InvalidOperationException("This thread has been deleted and cannot be used anymore.");
        }

        if (this._id is null)
        {
            await this.CreateAsync(cancellationToken).ConfigureAwait(false);
        }

        foreach (var message in this._chatHistory)
        {
            yield return message;
        }
    }
}
