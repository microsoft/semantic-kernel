// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents a thread that contains messages.
/// </summary>
public sealed class ChatThread : IChatThread
{
    /// <inheritdoc/>
    public string Id { get; private set; }

    /// <inheritdoc/>
    public IReadOnlyList<ChatMessage> Messages => Array.Empty<ChatMessage>(); // $$$

    private readonly IOpenAIRestContext _restContext;

    /// <summary>
    /// Create a new thread.
    /// </summary>
    /// <param name="restContext">An context for accessing OpenAI REST endpoint</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="ChatThread"> instance.</see></returns>
    public static async Task<ChatThread> CreateAsync(IOpenAIRestContext restContext, CancellationToken cancellationToken = default)
    {
        var threadModel =
            await restContext.CreateThreadAsync(cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure creating thread: no result.");

        return new ChatThread(threadModel.Id, restContext);
    }

    /// <summary>
    /// Retrieve an existing thread.
    /// </summary>
    /// <param name="restContext">An context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="ChatThread"> instance.</see></returns>
    public static async Task<ChatThread> GetAsync(IOpenAIRestContext restContext, string threadId, CancellationToken cancellationToken = default)
    {
        var threadModel =
            await restContext.GetThreadAsync(threadId, cancellationToken).ConfigureAwait(false) ??
            throw new SKException("Unexpected failure retrieving thread: no result.");

        return new ChatThread(threadModel.Id, restContext);
    }

    /// <inheritdoc/>
    public async Task AddUserMessageAsync(string message, CancellationToken cancellationToken = default)
    {
        var messageModel =
            await this._restContext.CreateMessageAsync(
                this.Id,
                ChatMessage.CreateUserMessage(message),
                cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<ChatMessage>> InvokeAsync(string assistantId, CancellationToken cancellationToken)
    {
        await this._restContext.CreateRunAsync(this.Id, assistantId, cancellationToken: cancellationToken).ConfigureAwait(false);

        return Array.Empty<ChatMessage>(); // $$$
    }

    public async Task<ChatMessage?> GetMessageAsync(string messageId, CancellationToken cancellationToken = default)
    {
        var message =
            await this._restContext.GetMessageAsync(this.Id, messageId, cancellationToken).ConfigureAwait(false) ??
            throw new ArgumentException("Uknown messageId", nameof(messageId));

        return GetMessage(message);
    }

    public async Task<IEnumerable<ChatMessage>> GetMessagesAsync(CancellationToken cancellationToken = default)
    {
        var messages = await this._restContext.GetMessagesAsync(this.Id, cancellationToken).ConfigureAwait(false);

        return messages.Data.Select(m => GetMessage(m));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatMessage"/> class.
    /// </summary>
    private ChatThread(string id, IOpenAIRestContext restContext)
    {
        this.Id = id;
        this._restContext = restContext;
    }

    private static ChatMessage GetMessage(ThreadMessageModel messageModel)
    {
        var content = (IEnumerable<ThreadMessageModel.ContentModel>)messageModel.Content;
        var text = content.First().Text?.Value ?? string.Empty; // $$$
        return new ChatMessage("text", text, messageModel.AssistantId, messageModel.Metadata);
    }
}
