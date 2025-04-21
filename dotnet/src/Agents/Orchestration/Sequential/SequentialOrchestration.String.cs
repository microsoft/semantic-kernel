// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Sequential;

/// <summary>
/// An orchestration that passes the input message to the first agent, and
/// then the subsequent result to the next agent, etc...
/// </summary>
public sealed partial class SequentialOrchestration : SequentialOrchestration<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SequentialOrchestration"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public SequentialOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] members)
        : base(runtime, members)
    {
        this.InputTransform = (string input) => ValueTask.FromResult(SequentialMessage.FromChat(new ChatMessageContent(AuthorRole.User, input)));
        this.ResultTransform = (SequentialMessage result) => ValueTask.FromResult(result.Message.ToString());
    }
}
