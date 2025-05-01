// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a step in a process that executes an agent.
/// </summary>
public class KernelProcessAgentExecutor : KernelProcessStep
{
    /// <summary>
    /// Invokes the agent with the provided definition.
    /// </summary>
    [KernelFunction]
    public void Invoke()
    {
    }
}
