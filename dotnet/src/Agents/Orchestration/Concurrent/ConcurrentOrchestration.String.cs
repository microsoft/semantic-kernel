// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public sealed class ConcurrentOrchestration : ConcurrentOrchestration<string, string[]>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ConcurrentOrchestration"/> class.
    /// </summary>
    /// <param name="members">The agents to be orchestrated.</param>
    public ConcurrentOrchestration(params Agent[] members)
        : base(members)
    {
        this.ResultTransform = (response, cancellationToken) => ValueTask.FromResult<string[]>([.. response.Select(r => r.Content ?? string.Empty)]);
    }
}
