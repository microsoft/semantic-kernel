// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents a conversation thread based on an instance of <see cref="ChatHistory"/> that is maanged inside this class.
/// </summary>
public class ChatHistoryAgentThread : AgentThread
{
    private readonly ChatHistory _chatHistory = new();
    private bool _isActive = false;
    private string? _id = null;

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
        this._isActive = true;
        this._id = id ?? Guid.NewGuid().ToString("N");
    }

    /// <inheritdoc />
    public override bool IsActive => this._isActive;

    /// <inheritdoc />
    public override string? Id => this._id;

    /// <inheritdoc/>
    public override Task<string> StartAsync(CancellationToken cancellationToken = default)
    {
        if (this._isActive)
        {
            throw new InvalidOperationException("You cannot start this thread, since the thread is already active.");
        }

        this._id = Guid.NewGuid().ToString("N");
        this._isActive = true;

        return Task.FromResult(this._id);
    }

    /// <inheritdoc/>
    public override Task EndAsync(CancellationToken cancellationToken = default)
    {
        if (!this._isActive)
        {
            throw new InvalidOperationException("This thread cannot be ended, since the thread is not currently active.");
        }

        this._chatHistory.Clear();
        this._id = null;
        this._isActive = false;

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public override Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        if (!this._isActive)
        {
            throw new InvalidOperationException("Messages cannot be added to this thread, since the thread is not currently active.");
        }

        this._chatHistory.Add(newMessage);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<ChatMessageContent> GetMessagesAsync(CancellationToken cancellationToken = default)
    {
        if (!this._isActive)
        {
            throw new InvalidOperationException("The chat history for this thread cannot be retrieved, since the thread is not currently active.");
        }

        return this._chatHistory.ToAsyncEnumerable();
    }
}
