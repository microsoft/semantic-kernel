// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An expression of the state of a group chat for use during agent selection.
/// This includes the chat history and a list of agent names.
/// </summary>
public sealed class GroupChatContext
{
    internal string? Selection { get; private set; }

    internal bool HasSelection => !string.IsNullOrWhiteSpace(this.Selection);

    /// <summary>
    /// The group chat history for consideration during agent selection.
    /// </summary>
    public IReadOnlyList<ChatMessageContent> History { get; }

    /// <summary>
    /// The agents that are part of the group chat.
    /// </summary>
    public ChatGroup Team { get; }

    internal GroupChatContext(ChatGroup team, IReadOnlyList<ChatMessageContent> history)
    {
        this.Team = team;
        this.History = history;
    }

    /// <summary>
    /// Indicates the next agent to be selected.  Not selecting will result
    /// in the chat terminating.  A null result can be used to indicate that
    /// the conversation is over, or it may signal that user input is needed.
    /// </summary>
    /// <param name="name">The agent to be selected.</param>
    /// <exception cref="KeyNotFoundException">When the specified agent isn't part of the group chat.</exception>
    public void SelectAgent(string name)
    {
        if (this.Team.ContainsKey(name))
        {
            this.Selection = name;
            return;
        }

        foreach (var team in this.Team)
        {
            if (team.Value.Name == name)
            {
                this.Selection = team.Key;
                return;
            }
        }

        throw new KeyNotFoundException($"Agent unknown to the group chat: {name}.");
    }
}
