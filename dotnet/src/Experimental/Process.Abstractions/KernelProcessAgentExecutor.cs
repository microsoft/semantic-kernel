// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a step in a process that executes an agent.
/// </summary>
public partial class KernelProcessAgentExecutor : KernelProcessStep<KernelProcessAgentExecutorState>
{
}

/// <summary>
/// State used by <see cref="KernelProcessAgentExecutor"/> to persist agent and thread details
/// </summary>
public sealed class KernelProcessAgentExecutorState
{
    /// <summary>
    /// Id of agent so it is reused if the same process is invoked again
    /// </summary>
    public string? AgentId { get; set; }

    /// <summary>
    /// Thread related information used for checking thread details by the specific agent
    /// </summary>
    public string? ThreadId { get; set; }
}
