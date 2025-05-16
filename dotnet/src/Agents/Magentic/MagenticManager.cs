// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Orchestration;

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// A manager that manages the flow of a Magentic style chat.
/// </summary>
public abstract class MagenticManager
{
    /// <summary>
    /// The default maximum number of resets allowed.
    /// </summary>
    internal const int DefaultMaximumResetsCount = 3;

    /// <summary>
    /// The default maximum number of stalls allowed.
    /// </summary>
    internal const int DefaultMaximumStallCount = 3;

    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticManager"/> class.
    /// </summary>
    protected MagenticManager() { }

    /// <summary>
    /// Gets or sets the maximum number of invocations allowed for the group chat manager.
    /// </summary>
    public int MaximumInvocationCount { get; init; } = int.MaxValue;

    /// <summary>
    /// Gets or sets the maximum number of resets allowed for the group chat manager.
    /// </summary>
    public int MaximumResetCount { get; init; } = DefaultMaximumResetsCount;

    /// <summary>
    /// Gets or sets the maximum number of stalls allowed for the group chat manager.
    /// </summary>
    public int MaximumStallCount { get; init; } = DefaultMaximumStallCount;

    /// <summary>
    /// Gets or sets the callback to be invoked for interactive input.
    /// </summary>
    public OrchestrationInteractiveCallback? InteractiveCallback { get; init; }

    /// <summary>
    /// Prepares the chat messages for the next step in the group chat process.
    /// </summary>
    /// <param name="context">The context for the manager.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>An array of chat message content to be processed.</returns>
    public abstract ValueTask<IList<ChatMessageContent>> PlanAsync(MagenticManagerContext context, CancellationToken cancellationToken);

    /// <summary>
    /// Resets the group chat state and prepares the initial chat messages.
    /// </summary>
    /// <param name="context">The context for the manager.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>An array of chat message content representing the reset state.</returns>
    public abstract ValueTask<IList<ChatMessageContent>> ReplanAsync(MagenticManagerContext context, CancellationToken cancellationToken);

    /// <summary>
    /// Evaluates the progress of the current group chat task.
    /// </summary>
    /// <param name="context">The context for the manager.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>A <see cref="MagenticProgressLedger"/> representing the progress evaluation.</returns>
    public abstract ValueTask<MagenticProgressLedger> EvaluateTaskProgressAsync(MagenticManagerContext context, CancellationToken cancellationToken = default);

    /// <summary>
    /// Prepares the final answer for the group chat task.
    /// </summary>
    /// <param name="context">The context for the manager.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>A <see cref="ChatMessageContent"/> representing the final answer.</returns>
    /// <remarks>
    /// The return type is <see cref="ChatMessageContent"/> to allow for rich content responses.
    /// </remarks>
    public abstract ValueTask<ChatMessageContent> PrepareFinalAnswerAsync(MagenticManagerContext context, CancellationToken cancellationToken = default);
}
