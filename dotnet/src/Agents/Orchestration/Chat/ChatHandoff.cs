// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Chat;

/// <summary>
/// Define how the chat history is translated into a singular response.
/// (i.e. What is the result of the chat?)
/// </summary>
public abstract class ChatHandoff
{
    /// <summary>
    /// Provide the final message to be returned to the user based on the entire chat history.
    /// </summary>
    /// <param name="history">The chat history</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>The final response</returns>
    public abstract ValueTask<ChatMessageContent> ProcessAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken);

    /// <summary>
    /// Default behavior for chat handoff: copy the final message in the history.
    /// </summary>
    public static readonly ChatHandoff Default = new DefaultChatHandoff();

    /// <summary>
    /// Provide final message, as default behavior.
    /// </summary>
    private sealed class DefaultChatHandoff : ChatHandoff
    {
        public override ValueTask<ChatMessageContent> ProcessAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken) => ValueTask.FromResult(history[^1]);
    }
}
