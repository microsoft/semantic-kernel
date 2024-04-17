// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// Interface for filtering actions during prompt rendering.
/// </summary>
[Experimental("SKEXP0110")]
public interface IAgentChatFilter
{
    /// <summary>
    /// Method which is executed before invoking agent.
    /// </summary>
    /// <param name="context">Data related to prompt before rendering.</param>
    void OnAgentInvoking(AgentChatFilterInvokingContext context);

    /// <summary>
    /// Method which is executed after invoking agent as each respons is processed.
    /// </summary>
    /// <param name="context">Data related to prompt after rendering.</param>
    void OnAgentInvoked(AgentChatFilterInvokedContext context);
}
