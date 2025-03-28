// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A container class for thread extension components that manages their lifecycle and interactions.
/// </summary>
public class ThreadExtensionsManager
{
    private readonly List<ThreadExtension> _threadExtensions = new();

    /// <summary>
    /// Gets the list of registered thread extensions.
    /// </summary>
    public virtual IReadOnlyList<ThreadExtension> ThreadExtensions => this._threadExtensions;

    /// <summary>
    /// Registers a new thread extensions.
    /// </summary>
    /// <param name="threadExtension">The thread extensions to register.</param>
    public virtual void RegisterThreadExtension(ThreadExtension threadExtension)
    {
        this._threadExtensions.Add(threadExtension);
    }

    /// <summary>
    /// Called when a new thread is created.
    /// </summary>
    /// <param name="threadId">The ID of the new thread.</param>
    /// <param name="inputText">The input text, typically a user ask.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public virtual async Task OnThreadCreateAsync(string threadId, string inputText, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ThreadExtensions.Select(x => x.OnThreadCreateAsync(threadId, inputText, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before a thread is deleted.
    /// </summary>
    /// <param name="threadId">The id of the thread that will be deleted.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public virtual async Task OnThreadDeleteAsync(string threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ThreadExtensions.Select(x => x.OnThreadDeleteAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// </summary>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public virtual async Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ThreadExtensions.Select(x => x.OnNewMessageAsync(newMessage, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before the AI is invoked
    /// </summary>
    /// <param name="newMessage">The most recent message that the AI is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation, containing the combined context from all thread extensions.</returns>
    public virtual async Task<string> OnAIInvocationAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        var subContexts = await Task.WhenAll(this.ThreadExtensions.Select(x => x.OnAIInvocationAsync(newMessage, cancellationToken)).ToList()).ConfigureAwait(false);
        return string.Join("\n", subContexts);
    }

    /// <summary>
    /// Registers plugins required by all thread extensions contained by this manager on the provided <see cref="Kernel"/>.
    /// </summary>
    /// <param name="kernel">The kernel to register the plugins on.</param>
    public virtual void RegisterPlugins(Kernel kernel)
    {
        foreach (var threadExtension in this.ThreadExtensions)
        {
            threadExtension.RegisterPlugins(kernel);
        }
    }
}
