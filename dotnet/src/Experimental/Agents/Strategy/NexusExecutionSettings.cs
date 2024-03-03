// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

/// <summary>
/// $$$
/// </summary>
/// <param name="message"></param>
/// <param name="cancellation"></param>
/// <returns></returns>
public delegate Task<bool> CompletionCriteriaCallback(ChatMessageContent message, CancellationToken cancellation); // $$$ HISTORY ???

/// <summary>
/// $$$
/// </summary>
public class NexusExecutionSettings
{
    /// <summary>
    /// $$$
    /// </summary>
    public static readonly NexusExecutionSettings Default = new() { MaximumIterations = 1 };

    /// <summary>
    /// $$$
    /// </summary>
    public int? MaximumIterations { get; set; }

    /// <summary>
    /// $$$
    /// </summary>
    public CompletionCriteriaCallback? CompletionCriteria { get; set; }
}
