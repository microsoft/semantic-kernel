// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// Describes a team of agents participating in a group chat.
/// </summary>
public class GroupChatTeam : Dictionary<string, (string Type, string Description)>;

/// <summary>
/// Extensions for <see cref="GroupChatTeam"/>.
/// </summary>
public static class ChatGroupExtensions
{
    /// <summary>
    /// Format the names of the agents in the team as a comma delimimted list.
    /// </summary>
    /// <param name="team">The agent team</param>
    /// <returns>A comma delimimted list of agent name.</returns>
    public static string FormatNames(this GroupChatTeam team) => string.Join(",", team.Select(t => t.Key));

    /// <summary>
    /// Format the names and descriptions of the agents in the team as a markdown list.
    /// </summary>
    /// <param name="team">The agent team</param>
    /// <returns>A markdown list of agent names and descriptions.</returns>
    public static string FormatList(this GroupChatTeam team) => string.Join("\n", team.Select(t => $"- {t.Key}: {t.Value.Description}"));
}
