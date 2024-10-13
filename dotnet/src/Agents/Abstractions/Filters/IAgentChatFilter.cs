// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// Interface for filtering actions during agent chat.
/// </summary>
public interface IAgentChatFilter
{
    /// <summary>
    /// Method which is executed before invoking agent.
    /// </summary>
    /// <param name="context">Data related to agent before invoking.</param>
    void OnAgentInvoking(AgentChatFilterInvokingContext context);

    /// <summary>
    /// Method which is executed after invoking agent as each response is processed.
    /// </summary>
    /// <param name="context">Data related to agent after invoking.</param>
    void OnAgentInvoked(AgentChatFilterInvokedContext context);
}
