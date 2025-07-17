// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="AggregateAIContextProvider"/>.
/// </summary>
[Experimental("SKEXP0130")]
public static class AggregateAIContextProviderExtensions
{
    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// </summary>
    /// <param name="aggregateAIContextProvider">The <see cref="AggregateAIContextProvider"/> to pass the new message to.</param>
    /// <param name="conversationId">The ID of the conversation/thread for the new message, if the conversation/thread has an ID.</param>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public static Task MessageAddingAsync(this AggregateAIContextProvider aggregateAIContextProvider, string? conversationId, ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        return aggregateAIContextProvider.MessageAddingAsync(conversationId, newMessage.ToChatMessage(), cancellationToken);
    }

    /// <summary>
    /// Called just before the Model/Agent/etc. is invoked
    /// </summary>
    /// <param name="aggregateAIContextProvider">The <see cref="AggregateAIContextProvider"/> to call.</param>
    /// <param name="newMessages">The most recent messages that the Model/Agent/etc. is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation, containing the combined context from all <see cref="AIContextProvider"/> objects.</returns>
    public static Task<AIContext> ModelInvokingAsync(this AggregateAIContextProvider aggregateAIContextProvider, ICollection<ChatMessageContent> newMessages, CancellationToken cancellationToken = default)
    {
        return aggregateAIContextProvider.ModelInvokingAsync([.. newMessages.Select(m => m.ToChatMessage())], cancellationToken);
    }
}
