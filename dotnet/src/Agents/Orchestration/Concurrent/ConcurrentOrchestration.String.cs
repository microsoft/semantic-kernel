// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public sealed class ConcurrentOrchestration : ConcurrentOrchestration<string, string[]>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ConcurrentOrchestration"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public ConcurrentOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] members)
        : base(runtime, members)
    {
        this.InputTransform = (string input) => ValueTask.FromResult(input.ToRequest());
        this.ResultTransform = (ConcurrentMessages.Result[] result) => ValueTask.FromResult<string[]>([.. result.Select(r => r.Message.Content ?? string.Empty)]);
    }
}
