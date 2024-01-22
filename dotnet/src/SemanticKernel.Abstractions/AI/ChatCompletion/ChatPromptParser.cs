// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Chat Prompt parser.
/// </summary>
internal static class ChatPromptParser
{
    private const string MessageTagName = "message";
    private const string RoleAttributeName = "role";
    private const string ImageTagName = "image";
    private const string TextTagName = "text";

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

        foreach (var node in nodes.Where(IsValidChatMessage))
        {
            (chatHistory ??= new()).Add(ParseChatNode(node));
        }

        return chatHistory is not null;
    }

    /// <summary>
    /// Parses a chat node and constructs a <see cref="ChatMessageContent"/> object.
    /// </summary>
    /// <param name="node">The prompt node to parse.</param>
    /// <returns><see cref="ChatMessageContent"/> object.</returns>
    private static ChatMessageContent ParseChatNode(PromptNode node)
    {
        ChatMessageContentItemCollection items = new();
        foreach (var childNode in node.ChildNodes.Where(childNode => childNode.Content is not null))
        {
            if (childNode.TagName.Equals(ImageTagName, StringComparison.OrdinalIgnoreCase))
            {
                items.Add(new ImageContent(new Uri(childNode.Content!)));
            }
            else if (childNode.TagName.Equals(TextTagName, StringComparison.OrdinalIgnoreCase))
            {
                items.Add(new TextContent(childNode.Content));
            }
        }

        if (items.Count == 1 && items[0] is TextContent textContent)
        {
            node.Content = textContent.Text;
            items.Clear();
        }

        var authorRole = new AuthorRole(node.Attributes[RoleAttributeName]);

        return items.Count > 0
            ? new ChatMessageContent(authorRole, items)
            : new ChatMessageContent(authorRole, node.Content);
    }

    /// <summary>
    /// Checks if <see cref="PromptNode"/> is valid chat message.
    /// </summary>
    /// <param name="node">Instance of <see cref="PromptNode"/>.</param>
    /// <remarks>
    /// A valid chat message is a node with the following structure:<br/>
    /// TagName = "message"<br/>
    /// Attributes = { "role" : "..." }<br/>
    /// optional one or more child nodes <image>...</image><br/>
    /// content not null or single child node <text>...</text>
    /// </remarks>
    private static bool IsValidChatMessage(PromptNode node)
    {
        return
            node.TagName.Equals(MessageTagName, StringComparison.OrdinalIgnoreCase) &&
            node.Attributes.ContainsKey(RoleAttributeName) &&
            IsValidChildNodes(node);
    }

    private static bool IsValidChildNodes(PromptNode node)
    {
        var textTagsCount = node.ChildNodes.Count(n => n.TagName.Equals(TextTagName, StringComparison.OrdinalIgnoreCase));
        return textTagsCount == 1 || (textTagsCount == 0 && node.Content is not null);
    }
}
