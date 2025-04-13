// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public sealed class BroadcastOrchestration : BroadcastOrchestration<string, string[]>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="BroadcastOrchestration"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public BroadcastOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] members)
        : base(runtime, members)
    {
        this.InputTransform = (string input) => input.ToBroadcastTask();
        this.ResultTransform = (BroadcastMessages.Result[] result) => [.. result.Select(r => r.Message.Content ?? string.Empty)];
    }
}
