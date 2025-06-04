// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Orchestration.Sequential;

/// <summary>
/// An orchestration that passes the input message to the first agent, and
/// then the subsequent result to the next agent, etc...
/// </summary>
public sealed class SequentialOrchestration : SequentialOrchestration<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SequentialOrchestration"/> class.
    /// </summary>
    /// <param name="members">The agents to be orchestrated.</param>
    public SequentialOrchestration(params Agent[] members)
        : base(members)
    {
    }
}
