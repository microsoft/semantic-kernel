// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Response from agent when called as a <see cref="KernelFunction"/>.
/// </summary>
public class AgentReference
{
    /// <summary>
    /// The agent identifier (which can be referenced in API endpoints).
    /// </summary>
    public string Id { get; internal set; } = string.Empty;

    /// <summary>
    /// Name of the agent
    /// </summary>
    public string? Name { get; internal set; }
}
