// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public sealed partial class HandoffOrchestration : HandoffOrchestration<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HandoffOrchestration"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public HandoffOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] members)
        : base(runtime, members)
    {
        this.InputTransform = (string input) => ValueTask.FromResult(HandoffMessage.FromChat(new ChatMessageContent(AuthorRole.User, input)));
        this.ResultTransform = (HandoffMessage result) => ValueTask.FromResult(result.Content.ToString());
    }
}
