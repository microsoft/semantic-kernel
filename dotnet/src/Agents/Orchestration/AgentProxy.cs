// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// A <see cref="ManagedAgent"/> built around a <see cref="Agents.Agent"/>.
/// </summary>
public abstract class AgentProxy : RuntimeAgent
{
    private AgentThread? _thread;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentProxy"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agents.Agent"/>.</param>
    protected AgentProxy(AgentId id, IAgentRuntime runtime, Agent agent)
        : base(id, runtime, agent.Description ?? throw new ArgumentException($"The agent description must be defined (#{agent.Name ?? agent.Id}).")) // %%%: DESCRIPTION Contract
    {
        this.Agent = agent;
    }

    /// <summary>
    /// %%%
    /// </summary>
    protected Agent Agent { get; }
}
