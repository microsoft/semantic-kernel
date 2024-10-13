// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// Context associated with to <see cref="IAgentChatFilter.OnAgentInvoking"/>.
/// </summary>
public sealed class AgentChatFilterInvokingContext : AgentChatFilterContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AgentChatFilterInvokingContext"/> class.
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="history"></param>
    internal AgentChatFilterInvokingContext(Agent agent, IReadOnlyList<ChatMessageContent> history)
        : base(agent, history)
    { }
}
