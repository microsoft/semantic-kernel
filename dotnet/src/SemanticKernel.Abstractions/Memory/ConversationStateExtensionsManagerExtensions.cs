// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="ConversationStateExtensionsManager"/>.
/// </summary>
[Experimental("SKEXP0001")]
public static class ConversationStateExtensionsManagerExtensions
{
    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// </summary>
    /// <param name="conversationStateExtensionsManager">The conversation state manager to pass the new message to.</param>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public static Task OnNewMessageAsync(this ConversationStateExtensionsManager conversationStateExtensionsManager, ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        return conversationStateExtensionsManager.OnNewMessageAsync(ChatCompletionServiceExtensions.ToChatMessage(newMessage), cancellationToken);
    }

    /// <summary>
    /// Called just before the AI is invoked
    /// </summary>
    /// <param name="conversationStateExtensionsManager">The conversation state manager to call.</param>
    /// <param name="newMessages">The most recent messages that the AI is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation, containing the combined context from all conversation state extensions.</returns>
    public static Task<string> OnAIInvocationAsync(this ConversationStateExtensionsManager conversationStateExtensionsManager, ICollection<ChatMessageContent> newMessages, CancellationToken cancellationToken = default)
    {
        return conversationStateExtensionsManager.OnAIInvocationAsync(newMessages.Select(ChatCompletionServiceExtensions.ToChatMessage).ToList(), cancellationToken);
    }
}
