// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public sealed partial class GroupChatOrchestration : GroupChatOrchestration<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GroupChatOrchestration"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="strategy">The strategy that determines how the chat shall proceed.</param>
    /// <param name="members">The agents to be orchestrated.</param>
    public GroupChatOrchestration(IAgentRuntime runtime, GroupChatStrategy strategy, params OrchestrationTarget[] members)
        : base(runtime, strategy, members)
    {
        this.InputTransform = (string input) => ValueTask.FromResult(new ChatMessageContent(AuthorRole.User, input).ToInputTask());
        this.ResultTransform = (ChatMessages.Result result) => ValueTask.FromResult(result.Message.ToString());
    }
}
