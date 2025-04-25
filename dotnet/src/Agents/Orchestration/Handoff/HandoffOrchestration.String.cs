// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// An orchestration that passes the input message to the first agent, and
/// then the subsequent result to the next agent, etc...
/// </summary>
public sealed class HandoffOrchestration : HandoffOrchestration<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HandoffOrchestration"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="handoffs">Defines the handoff connections for each agent.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public HandoffOrchestration(IAgentRuntime runtime, Dictionary<string, HandoffConnections> handoffs, params OrchestrationTarget[] members)
        : base(runtime, handoffs, members)
    {
        this.InputTransform = (string input) => ValueTask.FromResult(new HandoffMessages.InputTask { Message = new ChatMessageContent(AuthorRole.User, input) });
        this.ResultTransform = (HandoffMessages.Result result) => ValueTask.FromResult(result.Message.ToString());
    }
}
