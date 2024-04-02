// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Delegate definition for <see cref="ChatExecutionSettings.ContinuationStrategy"/>.
/// </summary>
/// <param name="agent">The agent actively interacting with the nexus.</param>
/// <param name="history">The chat history.</param>
/// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
/// <returns>True to continue.</returns>
public delegate Task<bool> ContinuationCriteriaCallback(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken);

/// <summary>
/// Delegate definition for <see cref="ChatExecutionSettings.SelectionStrategy"/>.
/// </summary>
/// <param name="agents">The agents participating in chat.</param>
/// <param name="history">The chat history.</param>
/// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
/// <returns>The agent who shall take the next turn.</returns>
public delegate Task<Agent?> SelectionCriteriaCallback(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken);

/// <summary>
/// Settings that affect behavior of <see cref="AgentChat"/>.
/// </summary>
/// <remarks>
/// Default behavior result in no agent selection or chat continuation.
/// </remarks>
public class ChatExecutionSettings
{
    /// <summary>
    /// Restrict number of turns to one, by default.
    /// </summary>
    public const int DefaultMaximumIterations = 1;

    /// <summary>
    /// The maximum number of agent interactions for a given nexus invocation.
    /// </summary>
    public int MaximumIterations { get; set; } = DefaultMaximumIterations;

    /// <summary>
    /// Optional strategy for evaluating the need to continue multiturn chat..
    /// </summary>
    /// <remarks>
    /// See <see cref="ContinuationStrategy"/>.
    /// </remarks>
    public ContinuationCriteriaCallback? ContinuationStrategy { get; set; }

    /// <summary>
    /// An optional strategy for selecting the next agent.
    /// </summary>
    /// <remarks>
    /// See <see cref="SelectionStrategy"/>.
    /// </remarks>
    public SelectionCriteriaCallback? SelectionStrategy { get; set; }
}
