// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization bound to a <see cref="ChatHistoryChannel"/>.
/// </summary>
/// <remarks>
/// NOTE: Enable <see cref="PromptExecutionSettings.FunctionChoiceBehavior"/> for agent plugins.
/// (<see cref="KernelAgent.Arguments"/>)
/// </remarks>
public abstract class ChatHistoryKernelAgent : KernelAgent
{
    /// <summary>
    /// Optionally specify a <see cref="IChatHistoryReducer"/> to reduce the history.
    /// </summary>
    /// <remarks>
    /// This is automatically applied to the history before invoking the agent, only when using
    /// an <see cref="AgentChat"/>.  It must be explicitly applied via <see cref="ReduceAsync"/>.
    /// </remarks>
    public IChatHistoryReducer? HistoryReducer { get; init; }

    /// <summary>
    /// Invoke the assistant to respond to the provided history.
    /// </summary>
    /// <param name="history">The conversation history.</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of response messages.</returns>
    public abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Invoke the assistant to respond to the provided history with streaming response.
    /// </summary>
    /// <param name="history">The conversation history.</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of response messages.</returns>
    public abstract IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Reduce the provided history
    /// </summary>
    /// <param name="history">The source history</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True if reduction has occurred.</returns>
    public Task<bool> ReduceAsync(ChatHistory history, CancellationToken cancellationToken = default) =>
        history.ReduceAsync(this.HistoryReducer, cancellationToken);

    /// <inheritdoc/>
    protected sealed override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(ChatHistoryChannel).FullName!;

        // Agents with different reducers shall not share the same channel.
        // Agents with the same or equivalent reducer shall share the same channel.
        if (this.HistoryReducer != null)
        {
            // Explicitly include the reducer type to eliminate the possibility of hash collisions
            // with custom implementations of IChatHistoryReducer.
            yield return this.HistoryReducer.GetType().FullName!;

            yield return this.HistoryReducer.GetHashCode().ToString(CultureInfo.InvariantCulture);
        }
    }

    /// <inheritdoc/>
    protected sealed override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        ChatHistoryChannel channel =
            new()
            {
                Logger = this.LoggerFactory.CreateLogger<ChatHistoryChannel>()
            };

        return Task.FromResult<AgentChannel>(channel);
    }
}
