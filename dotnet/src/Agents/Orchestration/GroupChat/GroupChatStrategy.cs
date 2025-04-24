// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// Strategy that determines how the group chat shall proceed.  Does it
/// select another agent for its response?  Is the response complete?
/// Is input requested?
/// </summary>
public abstract class GroupChatStrategy
{
    /// <summary>
    /// Callback used to evaluate the chat state and determine the next agent to be invoked.
    /// </summary>
    /// <param name="context">The group chat context</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>The next agent to respond.  Null results in no response.</returns>
    public delegate ValueTask CallbackAsync(GroupChatContext context, CancellationToken cancellationToken = default);

    /// <summary>
    /// Implicitly converts a <see cref="CallbackAsync"/> to a <see cref="GroupChatStrategy"/>.
    /// </summary>
    /// <param name="callback">The callback being cast</param>
    public static implicit operator GroupChatStrategy(CallbackAsync callback) => new CallbackStrategy(callback);

    /// <summary>
    /// Method used to evaluate the chat state and determine the next agent to be invoked.
    /// </summary>
    /// <param name="context">The group chat context</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    public abstract ValueTask SelectAsync(GroupChatContext context, CancellationToken cancellationToken = default);

    private sealed class CallbackStrategy(CallbackAsync selectCallback) : GroupChatStrategy
    {
        public override ValueTask SelectAsync(GroupChatContext context, CancellationToken cancellationToken = default) =>
            selectCallback.Invoke(context, cancellationToken);
    }
}
