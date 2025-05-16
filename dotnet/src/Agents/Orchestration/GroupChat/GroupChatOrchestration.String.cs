// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public sealed class GroupChatOrchestration : GroupChatOrchestration<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GroupChatOrchestration"/> class.
    /// </summary>
    /// <param name="manager">The manages the flow of the group-chat.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public GroupChatOrchestration(GroupChatManager manager, params Agent[] members)
        : base(manager, members)
    {
    }
}
