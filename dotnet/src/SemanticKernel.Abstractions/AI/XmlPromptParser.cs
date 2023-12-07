// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Xml;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class to parse text prompt from XML format.
/// </summary>
internal static class XmlPromptParser
{
    /// <summary>
    /// Parses text prompt and sets output as collection of <see cref="PromptNode"/> instances.
    /// </summary>
    /// <param name="prompt">Text prompt to parse.</param>
    /// <param name="result">Parsing output as collection of <see cref="PromptNode"/> instances.</param>
    /// <returns>Returns true if parsing was successful, otherwise false.</returns>
    public static bool TryParse(string prompt, [NotNullWhen(true)] out List<PromptNode>? result)
    {
        result = null;

        // The below parsing is _very_ expensive, especially when the content is not valid XML and an
        // exception is thrown. Try to avoid it in the common case where the prompt is obviously not XML.
        // To be valid XML, at a minimum:
        // - the string would need to be non-null
        // - it would need to contain a the start of a tag
        // - it would need to contain a closing tag, which could include either </ or />
        int startPos;
        if (prompt is null ||
            (startPos = prompt.IndexOf('<')) < 0 ||
            (prompt.IndexOf("</", startPos + 1, StringComparison.Ordinal) < 0 &&
             prompt.IndexOf("/>", startPos + 1, StringComparison.Ordinal) < 0))
        {
            return false;
        }

        var xmlDocument = new XmlDocument();
        try
        {
            xmlDocument.LoadXml($"<root>{prompt}</root>");
        }
        catch (XmlException)
        {
            return false;
        }

        foreach (XmlNode node in xmlDocument.DocumentElement!.ChildNodes)
        {
            if (GetPromptNode(node) is { } childPromptNode)
            {
                (result ??= new()).Add(childPromptNode);
            }
        }

        return result is not null;
    }

    /// <summary>
    /// Gets an instance of <see cref="PromptNode"/> from <see cref="XmlNode"/> and child nodes recursively.
    /// </summary>
    /// <param name="node">Instance of <see cref="XmlNode"/> class.</param>
    private static PromptNode? GetPromptNode(XmlNode node)
    {
        if (node.NodeType != XmlNodeType.Element)
        {
            return null;
        }

        var nodeContent = node.InnerText.Trim();

        var promptNode = new PromptNode(node.Name)
        {
            Content = !string.IsNullOrEmpty(nodeContent) ? nodeContent : null
        };

        if (node.Attributes is not null)
        {
            foreach (XmlAttribute item in node.Attributes)
            {
                promptNode.Attributes.Add(item.Name, item.Value);
            }
        }

        foreach (XmlNode childNode in node.ChildNodes)
        {
            var childPromptNode = GetPromptNode(childNode);

            if (childPromptNode != null)
            {
                promptNode.ChildNodes.Add(childPromptNode);
            }
        }

        return promptNode;
    }
}
