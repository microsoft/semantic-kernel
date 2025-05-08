// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="AIContextBehaviorsManager"/>.
/// </summary>
[Experimental("SKEXP0130")]
public static class AIContextBehaviorsManagerExtensions
{
    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// </summary>
    /// <param name="aiContextBehaviorsManager">The <see cref="AIContextBehaviorsManager"/> to pass the new message to.</param>
    /// <param name="threadId">The ID of the thread for the new message, if the thread has an ID.</param>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public static Task OnNewMessageAsync(this AIContextBehaviorsManager aiContextBehaviorsManager, string? threadId, ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        return aiContextBehaviorsManager.OnNewMessageAsync(threadId, ChatCompletionServiceExtensions.ToChatMessage(newMessage), cancellationToken);
    }

    /// <summary>
    /// Called just before the Model/Agent/etc. is invoked
    /// </summary>
    /// <param name="aiContextBehaviorsManager">The <see cref="AIContextBehaviorsManager"/> to call.</param>
    /// <param name="newMessages">The most recent messages that the Model/Agent/etc. is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation, containing the combined context from all <see cref="AIContextBehavior"/> objects.</returns>
    public static Task<string> OnModelInvokeAsync(this AIContextBehaviorsManager aiContextBehaviorsManager, ICollection<ChatMessageContent> newMessages, CancellationToken cancellationToken = default)
    {
        return aiContextBehaviorsManager.OnModelInvokeAsync(newMessages.Select(ChatCompletionServiceExtensions.ToChatMessage).ToList(), cancellationToken);
    }
}
