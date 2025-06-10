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
#if NET
            prompt.Contains(MessageTagStart, StringComparison.OrdinalIgnoreCase) &&
#else
            prompt.IndexOf(MessageTagStart, StringComparison.OrdinalIgnoreCase) >= 0 &&
#endif
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
            (chatHistory ??= []).Add(ParseChatNode(node));
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
        ChatMessageContentItemCollection items = [];
        foreach (var childNode in node.ChildNodes.Where(childNode => childNode.Content is not null))
        {
            if (s_contentFactoryMapping.TryGetValue(childNode.TagName.ToUpperInvariant(), out var createBinaryContent))
            {
                childNode.Attributes.TryGetValue("mimetype", out var mimeType);
                items.Add(createBinaryContent(childNode.Content!, mimeType));
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
    /// Creates a new instance of <typeparamref name="T"/> from a data URI.
    /// </summary>
    /// <typeparam name="T">Type of <see cref="BinaryContent"/> to create.</typeparam>
    /// <param name="content">Base64 encoded content or URI.</param>
    /// <param name="mimeType">Optional MIME type of the content.</param>
    /// <returns>A new instance of <typeparamref name="T"/> with <paramref name="content"/></returns>
    private static T CreateBinaryContent<T>(string content, string? mimeType) where T : BinaryContent, new()
    {
        return (content.StartsWith("data:", StringComparison.OrdinalIgnoreCase)) ? new T { DataUri = content } : new T { Uri = new Uri(content), MimeType = mimeType };
    }

    /// <summary>
    /// Factory for creating a <see cref="KernelContent"/> instance based on the tag name.
    /// </summary>
    private static readonly Dictionary<string, Func<string, string?, KernelContent>> s_contentFactoryMapping = new()
    {
        { TextTagName, (content, _) => new TextContent(content) },
        { ImageTagName, CreateBinaryContent<ImageContent> },
        { AudioTagName, CreateBinaryContent<AudioContent> },
        { BinaryTagName, CreateBinaryContent<BinaryContent> }
    };

    /// <summary>
    /// Checks if <see cref="PromptNode"/> is valid chat message.
    /// </summary>
    /// <param name="node">Instance of <see cref="PromptNode"/>.</param>
    /// <remarks>
    /// A valid chat message is a node with the following structure:
    /// <list type="bullet">
    /// <item><description>TagName = "message"</description></item>
    /// <item><description>Attributes = { "role" : "..." }</description></item>
    /// <item><description>optional one or more child nodes &lt;image&gt;...&lt;/image&gt;</description></item>
    /// <item><description>optional one or more child nodes &lt;text&gt;...&lt;/text&gt;</description></item>
    /// <item><description>optional one or more child nodes &lt;audio&gt;...&lt;/audio&gt;</description></item>
    /// <item><description>optional one or more child nodes &lt;binary&gt;...&lt;/binary&gt;</description></item>
    /// </list>
    /// </remarks>
    private static bool IsValidChatMessage(PromptNode node)
    {
        return
            node.TagName.Equals(MessageTagName, StringComparison.OrdinalIgnoreCase) &&
            node.Attributes.ContainsKey(RoleAttributeName);
    }

    private const string MessageTagName = "message";
    private const string RoleAttributeName = "role";
    private const string ImageTagName = "IMAGE";
    private const string TextTagName = "TEXT";
    private const string AudioTagName = "AUDIO";
    private const string BinaryTagName = "BINARY";
}
