// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A container class for <see cref="ConversationStateExtension"/> objects that manages their lifecycle and interactions.
/// </summary>
[Experimental("SKEXP0130")]
public class ConversationStateExtensionsManager
{
    private readonly List<ConversationStateExtension> _conversationStateExtensions = new();

    /// <summary>
    /// Gets the list of registered conversation state extensions.
    /// </summary>
    public virtual IReadOnlyList<ConversationStateExtension> ConversationStateExtensions => this._conversationStateExtensions;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationStateExtensionsManager"/> class.
    /// </summary>
    public ConversationStateExtensionsManager()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationStateExtensionsManager"/> class with the specified conversation state extensions.
    /// </summary>
    /// <param name="conversationtStateExtensions">The conversation state extensions to add to the manager.</param>
    public ConversationStateExtensionsManager(IEnumerable<ConversationStateExtension> conversationtStateExtensions)
    {
        this._conversationStateExtensions.AddRange(conversationtStateExtensions);
    }

    /// <summary>
    /// Registers a new conversation state extensions.
    /// </summary>
    /// <param name="conversationtStateExtension">The conversation state extensions to register.</param>
    public virtual void RegisterThreadExtension(ConversationStateExtension conversationtStateExtension)
    {
        this._conversationStateExtensions.Add(conversationtStateExtension);
    }

    /// <summary>
    /// Called when a new thread is created.
    /// </summary>
    /// <param name="threadId">The ID of the new thread.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public virtual async Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnThreadCreatedAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before a thread is deleted.
    /// </summary>
    /// <param name="threadId">The id of the thread that will be deleted.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public virtual async Task OnThreadDeleteAsync(string threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnThreadDeleteAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// </summary>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public virtual async Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnNewMessageAsync(newMessage, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before the AI is invoked
    /// </summary>
    /// <param name="newMessages">The most recent messages that the AI is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation, containing the combined context from all conversation state extensions.</returns>
    public virtual async Task<string> OnAIInvocationAsync(ICollection<ChatMessageContent> newMessages, CancellationToken cancellationToken = default)
    {
        var subContexts = await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnAIInvocationAsync(newMessages, cancellationToken)).ToList()).ConfigureAwait(false);
        return string.Join("\n", subContexts);
    }

    /// <summary>
    /// Registers plugins required by all conversation state extensions contained by this manager on the provided <see cref="Kernel"/>.
    /// </summary>
    /// <param name="kernel">The kernel to register the plugins on.</param>
    public virtual void RegisterPlugins(Kernel kernel)
    {
        foreach (var threadExtension in this.ConversationStateExtensions)
        {
            threadExtension.RegisterPlugins(kernel);
        }
    }
}
