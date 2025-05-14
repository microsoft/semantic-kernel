// Copyright (c) Microsoft. All rights reserved.

using System.Linq;

#if NETCOREAPP
using System.Threading.Tasks;
#endif

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
        this.ResultTransform =
            (response, cancellationToken) =>
            {
                string[] result = [.. response.Select(r => r.Content ?? string.Empty)];
#if !NETCOREAPP
                return result.AsValueTask();
#else
                return ValueTask.FromResult(result);
#endif
            };
    }
}
