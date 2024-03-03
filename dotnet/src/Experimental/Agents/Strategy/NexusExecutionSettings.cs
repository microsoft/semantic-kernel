// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

/// <summary>
/// Delegate definition for <see cref="NexusExecutionSettings.CompletionCriteria"/>.
/// </summary>
/// <param name="history">The chat history.</param>
/// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
/// <returns>True when complete.</returns>
public delegate Task<bool> CompletionCriteriaCallback(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken);

/// <summary>
/// Settings that affect behavior of <see cref="StrategyNexus"/>.
/// </summary>
public class NexusExecutionSettings
{
    /// <summary>
    /// The default <see cref="NexusExecutionSettings"/>.
    /// </summary>
    public static readonly NexusExecutionSettings Default = new() { MaximumIterations = 1 };

    /// <summary>
    /// The maximum number of agent interactions for a given nexus invocation.
    /// </summary>
    public int? MaximumIterations { get; set; }

    /// <summary>
    /// Completion evaulation criteria.
    /// </summary>
    /// <remarks>
    /// See <see cref="CompletionStrategy"/>.
    /// </remarks>
    public CompletionCriteriaCallback? CompletionCriteria { get; set; }
}
