// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Optional parameters for agent invocation.
/// </summary>
public class AgentInvokeOptions
{
    /// <summary>
    /// Gets or sets any instructions, in addition to those that were provided to the agent
    /// initially, that need to be added to the prompt for this invocation only.
    /// </summary>
    public string AdditionalInstructions { get; init; } = string.Empty;
}
