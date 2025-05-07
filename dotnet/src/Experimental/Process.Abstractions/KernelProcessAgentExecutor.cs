// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a step in a process that executes an agent.
/// </summary>
public class KernelProcessAgentExecutor : KernelProcessStep
{
    /// <summary>
    /// SK Function names in this SK Step as entry points
    /// </summary>
    public static class ProcessFunctions
    {
        /// <summary>
        /// Function name used to emit events externally
        /// </summary>
        public const string Invoke = nameof(Invoke);
    }

    /// <summary>
    /// Invokes the agent with the provided definition.
    /// </summary>
    [KernelFunction]
    public void Invoke()
    {
    }
}
