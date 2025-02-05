// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.AI.CrewAI;

/// <summary>
/// Represents the state of a CrewAI Crew kickoff.
/// </summary>
public enum CrewAIKickoffState
{
    /// <summary>
    /// The kickoff is pending and has not started yet.
    /// </summary>
    Pending,

    /// <summary>
    /// The kickoff has started.
    /// </summary>
    Started,

    /// <summary>
    /// The kickoff is currently running.
    /// </summary>
    Running,

    /// <summary>
    /// The kickoff completed successfully.
    /// </summary>
    Success,

    /// <summary>
    /// The kickoff failed.
    /// </summary>
    Failed,

    /// <summary>
    /// The kickoff has failed.
    /// </summary>
    Failure,

    /// <summary>
    /// The kickoff was not found.
    /// </summary>
    NotFound
}
