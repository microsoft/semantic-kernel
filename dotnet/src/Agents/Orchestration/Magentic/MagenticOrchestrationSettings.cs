// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Orchestration.Magentic;

/// <summary>
/// Settings associated with the <see cref="MagenticOrchestration{TInput, TOutput}"/>.
/// </summary>
public class MagenticOrchestrationSettings
{
    private const int DefaultMaximumRetryCount = 2;
    private const int DefaultMaximumStallCount = 3;

    /// <summary>
    /// The default settings.
    /// </summary>
    public static readonly MagenticOrchestrationSettings Default = new();

    /// <summary>
    /// The maximum number of retry attempts when the task execution faulters.
    /// </summary>
    public int MaximumRetryCount { get; init; } = DefaultMaximumRetryCount;

    /// <summary>
    /// The maximum number of stalls to allow before failing the orchestration.
    /// </summary>
    public int MaximumStallCount { get; init; } = DefaultMaximumStallCount;

    /// <summary>
    /// Identifies the service used by the orchestration manager when not default.
    /// </summary>
    public string? ServiceId { get; init; }
}
