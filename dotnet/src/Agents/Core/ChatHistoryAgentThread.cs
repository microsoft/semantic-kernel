// Copyright (c) Microsoft. All rights reserved.

using System;
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
    private string? _threadId = null;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryAgentThread"/> class.
    /// </summary>
    public ChatHistoryAgentThread()
    {
    }

    /// <inheritdoc />
    public override bool IsActive => this._isActive;

    /// <inheritdoc />
    public override string? ThreadId => this._threadId;

    /// <inheritdoc/>
    public override Task<string> StartThreadAsync(CancellationToken cancellationToken = default)
    {
        if (this._isActive)
        {
            throw new InvalidOperationException("You cannot start this thread, since the thread is already active.");
        }

        this._threadId = Guid.NewGuid().ToString("N");
        this._isActive = true;

        return Task.FromResult(this._threadId);
    }

    /// <inheritdoc/>
    public override Task EndThreadAsync(CancellationToken cancellationToken = default)
    {
        if (!this._isActive)
        {
            throw new InvalidOperationException("This thread cannot be ended, since the thread is not currently active.");
        }

        this._chatHistory.Clear();
        this._threadId = null;
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
    public Task<ChatHistory> RetrieveCurrentChatHistoryAsync(CancellationToken cancellationToken = default)
    {
        if (!this._isActive)
        {
            throw new InvalidOperationException("The chat history for this thread cannot be retrieved, since the thread is not currently active.");
        }

        return Task.FromResult(this._chatHistory);
    }
}
