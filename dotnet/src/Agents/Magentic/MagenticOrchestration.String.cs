// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public sealed class MagenticOrchestration : MagenticOrchestration<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticOrchestration"/> class.
    /// </summary>
    /// <param name="manager">The manages the flow of the group-chat.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public MagenticOrchestration(MagenticManager manager, params Agent[] members)
        : base(manager, members)
    {
    }
}
