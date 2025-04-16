// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Magentic;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public sealed partial class MagenticOrchestration : MagenticOrchestration<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticOrchestration"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public MagenticOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] members)
        : base(runtime, members)
    {
        this.InputTransform = (string input) => ValueTask.FromResult(new ChatMessageContent(AuthorRole.User, input).ToInputTask());
        this.ResultTransform = (ChatMessages.Result result) => ValueTask.FromResult(result.Message.ToString());
    }
}
