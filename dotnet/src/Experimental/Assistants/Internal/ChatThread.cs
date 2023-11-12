// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Internal;

/// <summary>
/// Represents a thread that contains messages.
/// </summary>
internal sealed class ChatThread : IChatThread
{
    /// <inheritdoc/>
    public string Id { get; private set; }

    /// <inheritdoc/>
    public IReadOnlyList<IChatMessage> Messages => this._messages.AsReadOnly();

    private readonly IOpenAIRestContext _restContext;
    private readonly List<IChatMessage> _messages;
    private readonly Dictionary<string, IChatMessage> _messageIndex;

    /// <summary>
    /// Create a new thread.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="ChatThread"> instance.</see></returns>
    public static async Task<IChatThread> CreateAsync(IOpenAIRestContext restContext, CancellationToken cancellationToken = default)
    {
        var threadModel =
            await restContext.CreateThreadModelAsync(cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure creating thread: no result.");

        return new ChatThread(threadModel, messageListModel: null, restContext);
    }

    /// <summary>
    /// Retrieve an existing thread.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="ChatThread"> instance.</see></returns>
    public static async Task<IChatThread> GetAsync(IOpenAIRestContext restContext, string threadId, CancellationToken cancellationToken = default)
    {
        var threadModel =
            await restContext.GetThreadModelAsync(threadId, cancellationToken).ConfigureAwait(false) ??
            throw new SKException($"Unexpected failure retrieving thread: no result. ({threadId})");

        var messageListModel =
            await restContext.GetMessagesAsync(threadId, cancellationToken).ConfigureAwait(false) ??
            throw new SKException($"Unexpected failure retrieving thread: no result. ({threadId})");

        return new ChatThread(threadModel, messageListModel, restContext);
    }

    /// <inheritdoc/>
    public async Task<IChatMessage> AddUserMessageAsync(string message, CancellationToken cancellationToken = default)
    {
        var messageModel =
            await this._restContext.CreateUserTextMessageAsync(
                this.Id,
                message,
                cancellationToken).ConfigureAwait(false);

        return this.AddMessage(messageModel);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<IChatMessage>> InvokeAsync(string assistantId, string? instructions, CancellationToken cancellationToken)
    {
        var runModel = await this._restContext.CreateRunAsync(this.Id, assistantId, instructions, cancellationToken).ConfigureAwait(false);

        var run = new ChatRun(runModel, this._restContext);
        var results = await run.GetResultAsync(cancellationToken).ConfigureAwait(false);

        var messages = await this.GetMessagesAsync(results, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);

        return messages;
    }

    private async IAsyncEnumerable<IChatMessage> GetMessagesAsync(
        IList<string> messageIds,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await Task.Delay(0, cancellationToken).ConfigureAwait(false);
        var messages = await this._restContext.GetMessagesAsync(this.Id, messageIds, cancellationToken: cancellationToken).ConfigureAwait(false);
        foreach (var message in messages)
        {
            yield return this.AddMessage(message);
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatThread"/> class.
    /// </summary>
    private ChatThread(
        ThreadModel threadModel,
        ThreadMessageListModel? messageListModel,
        IOpenAIRestContext restContext)
    {
        this.Id = threadModel.Id;
        this._messages = ((IList<ThreadMessageModel>?)messageListModel?.Data ?? Array.Empty<ThreadMessageModel>()).Select(m => (IChatMessage)new ChatMessage(m)).ToList();
        this._messageIndex = this._messages.ToDictionary(m => m.Id);
        this._restContext = restContext;
    }

    private ChatMessage AddMessage(ThreadMessageModel messageModel)
    {
        var message = new ChatMessage(messageModel);

        this._messages.Add(message);
        this._messageIndex.Add(message.Id, message);

        return message;
    }
}
