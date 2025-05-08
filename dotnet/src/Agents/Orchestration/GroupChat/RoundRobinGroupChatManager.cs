// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// A <see cref="GroupChatManager"/> that selects agents in a round-robin fashion.
/// </summary>
/// <remarks>
/// Subclass this class to customize filter and user interaction behavior.
/// </remarks>
public class RoundRobinGroupChatManager : GroupChatManager
{
    private int _currentAgentIndex;

    /// <inheritdoc/>
    public override ValueTask<GroupChatManagerResult<string>> FilterResults(ChatHistory history, CancellationToken cancellationToken = default) =>
        ValueTask.FromResult(new GroupChatManagerResult<string>(history.LastOrDefault()?.Content ?? string.Empty) { Reason = "Default result filter provides the final chat message." });

    /// <inheritdoc/>
    public override ValueTask<GroupChatManagerResult<string>> SelectNextAgent(ChatHistory history, ChatGroup team, CancellationToken cancellationToken = default)
    {
        string nextAgent = team.Skip(this._currentAgentIndex).First().Key;
        this._currentAgentIndex = (this._currentAgentIndex + 1) % team.Count;
        return ValueTask.FromResult(new GroupChatManagerResult<string>(nextAgent) { Reason = $"Selected agent at index: {this._currentAgentIndex}" });
    }

    /// <inheritdoc/>
    public override ValueTask<GroupChatManagerResult<bool>> ShouldRequestUserInput(ChatHistory history, CancellationToken cancellationToken = default) =>
        ValueTask.FromResult(new GroupChatManagerResult<bool>(false) { Reason = "The default round-robin group chat manager does not request user input." });
}
