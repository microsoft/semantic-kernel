// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Optional parameters for BedrockAgent invocation.
/// </summary>
public sealed class BedrockAgentInvokeOptions : AgentInvokeOptions
{
    /// <summary>
    /// Gets or sets the alias ID of the agent to invoke.
    /// </summary>
    public string? AgentAliasId { get; set; }

    /// <summary>
    /// Enable trace to inspect the agent's thought process
    /// </summary>
    public bool EnableTrace { get; set; }
}
