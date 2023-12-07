// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Chat Prompt parser.
/// </summary>
internal static class ChatPromptParser
{
    private const string MessageTagName = "message";
    private const string RoleAttributeName = "role";

    /// <summary>
    /// Parses collection of <see cref="PromptNode"/> instances and sets output as <see cref="ChatHistory"/>.
    /// </summary>
    /// <param name="nodes">Collection of <see cref="PromptNode"/> to parse.</param>
    /// <param name="chatHistory">Parsing output as <see cref="ChatHistory"/>.</param>
    /// <returns>Returns true if parsing was successful, otherwise false.</returns>
    public static bool TryParse(List<PromptNode> nodes, out ChatHistory chatHistory)
    {
        chatHistory = new ChatHistory();

        foreach (var node in nodes)
        {
            if (IsValidChatMessage(node))
            {
                var role = node.Attributes[RoleAttributeName];
                var content = node.Content!;

                chatHistory.AddMessage(new AuthorRole(role), content);
            }
        }

        return chatHistory.Count != 0;
    }

    /// <summary>
    /// Checks if <see cref="PromptNode"/> is valid chat message.
    /// </summary>
    /// <param name="node">Instance of <see cref="PromptNode"/>.</param>
    private static bool IsValidChatMessage(PromptNode node)
    {
        return
            node.TagName.Equals(MessageTagName, StringComparison.OrdinalIgnoreCase) &&
            node.Attributes.ContainsKey(RoleAttributeName) &&
            node.Content is not null;
    }
}
