// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public sealed partial class HandoffOrchestration
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HandoffOrchestration"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public static HandoffOrchestration<ChatMessageContent, ChatMessageContent> ForMessage(IAgentRuntime runtime, params OrchestrationTarget[] members) // %%% CONSIDER
    {
        return new HandoffOrchestration<ChatMessageContent, ChatMessageContent>(runtime, members)
        {
            InputTransform = HandoffMessage.FromChat,
            ResultTransform = (HandoffMessage result) => result.Content,
        };
    }
}
