// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// Context associated with to <see cref="IAgentChatFilter.OnAgentInvoked"/>.
/// </summary>
public sealed class AgentChatFilterInvokedContext : AgentChatFilterContext
{
    /// <summary>
    /// %%%
    /// </summary>
    public ChatMessageContent Message { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentChatFilterInvokedContext"/> class.
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="history"></param>
    /// <param name="message"></param>
    internal AgentChatFilterInvokedContext(Agent agent, IReadOnlyList<ChatMessageContent> history, ChatMessageContent message)
        : base(agent, history)
    {
        this.Message = message;
    }
}
