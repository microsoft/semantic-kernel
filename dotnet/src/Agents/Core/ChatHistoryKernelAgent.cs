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
/// NOTE: Enable OpenAIPromptExecutionSettings.ToolCallBehavior for agent plugins.
/// (<see cref="ChatHistoryKernelAgent.Arguments"/>)
/// </remarks>
public abstract class ChatHistoryKernelAgent : KernelAgent
{
    /// <summary>
    /// Optional arguments for the agent.
    /// </summary>
    public KernelArguments? Arguments { get; init; }

    /// <inheritdoc/>
    public IChatHistoryReducer? HistoryReducer { get; init; }

    /// <inheritdoc/>
    public abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);

    /// <inheritdoc/>
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
    /// <returns></returns>
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
