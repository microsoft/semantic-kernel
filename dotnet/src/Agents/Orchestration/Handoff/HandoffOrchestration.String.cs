// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// An orchestration that passes the input message to the first agent, and
/// then the subsequent result to the next agent, etc...
/// </summary>
public sealed class HandoffOrchestration : HandoffOrchestration<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HandoffOrchestration"/> class.
    /// </summary>
    /// <param name="handoffs">Defines the handoff connections for each agent.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public HandoffOrchestration(Dictionary<string, HandoffConnections> handoffs, params Agent[] members)
        : base(handoffs, members)
    {
    }
}
