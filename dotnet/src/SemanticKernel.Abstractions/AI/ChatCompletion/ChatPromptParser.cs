// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Chat Prompt parser.
/// </summary>
internal static class ChatPromptParser
{
    private const string MessageTagName = "message";
    private const string RoleAttributeName = "role";

    /// <summary>
    /// Parses a prompt for an XML representation of a <see cref="ChatHistory"/>.
    /// </summary>
    /// <param name="prompt">The prompt to parse.</param>
    /// <param name="chatHistory">The parsed <see cref="ChatHistory"/>, or null if it couldn't be parsed.</param>
    /// <returns>true if the history could be parsed; otherwise, false.</returns>
    public static bool TryParse(string prompt, [NotNullWhen(true)] out ChatHistory? chatHistory)
    {
        // Parse the input string into nodes and then those nodes into a chat history.
        // The XML parsing is expensive, so we do a quick up-front check to make sure
        // the text contains "<message", as that's required in any valid XML prompt.
        const string MessageTagStart = "<" + MessageTagName;
        if (prompt is not null &&
            prompt.IndexOf(MessageTagStart, StringComparison.OrdinalIgnoreCase) >= 0 &&
            XmlPromptParser.TryParse(prompt, out var nodes) &&
            TryParse(nodes, out chatHistory))
        {
            return true;
        }

        chatHistory = null;
        return false;
    }

    /// <summary>
    /// Parses collection of <see cref="PromptNode"/> instances and sets output as <see cref="ChatHistory"/>.
    /// </summary>
    /// <param name="nodes">Collection of <see cref="PromptNode"/> to parse.</param>
    /// <param name="chatHistory">Parsing output as <see cref="ChatHistory"/>.</param>
    /// <returns>Returns true if parsing was successful, otherwise false.</returns>
    private static bool TryParse(List<PromptNode> nodes, [NotNullWhen(true)] out ChatHistory? chatHistory)
    {
        chatHistory = null;

        foreach (var node in nodes)
        {
            if (IsValidChatMessage(node))
            {
                var role = node.Attributes[RoleAttributeName];
                var content = node.Content!;

                (chatHistory ??= new()).AddMessage(new AuthorRole(role), content);
            }
        }

        return chatHistory is not null;
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
