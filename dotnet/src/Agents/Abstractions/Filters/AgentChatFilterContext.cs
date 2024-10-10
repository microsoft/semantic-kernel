// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// Base class with data related to <see cref="IAgentChatFilter"/>.
/// </summary>
public abstract class AgentChatFilterContext
{
    /// <summary>
    /// Gets the <see cref="Agent"/> with which this filter is associated.
    /// </summary>
    public Agent Agent { get; }

    /// <summary>
    /// Gets the message history with which this filter is associated.
    /// </summary>
    public IReadOnlyList<ChatMessageContent> History { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentChatFilterContext"/> class.
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="history"></param>
    internal AgentChatFilterContext(Agent agent, IReadOnlyList<ChatMessageContent> history)
    {
        this.Agent = agent;
        this.History = history;
    }
}
