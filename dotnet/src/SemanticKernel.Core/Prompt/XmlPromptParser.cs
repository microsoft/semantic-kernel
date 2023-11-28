// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Xml;

namespace Microsoft.SemanticKernel.Prompt;

/// <summary>
/// Class to parse text prompt from XML format.
/// </summary>
public static class XmlPromptParser
{
    /// <summary>
    /// Parses text prompt and sets output as collection of <see cref="PromptNode"/> instances.
    /// </summary>
    /// <param name="prompt">Text prompt to parse.</param>
    /// <param name="result">Parsing output as collection of <see cref="PromptNode"/> instances.</param>
    /// <returns>Returns true if parsing was successful, otherwise false.</returns>
    public static bool TryParse(string prompt, out List<PromptNode> result)
    {
        result = new List<PromptNode>();
        var xmlDocument = new XmlDocument();
        var xmlString = $"<root>{prompt}</root>";

        try
        {
            xmlDocument.LoadXml(xmlString);
        }
        catch (XmlException)
        {
            return false;
        }

        foreach (XmlNode node in xmlDocument.DocumentElement!.ChildNodes)
        {
            var childPromptNode = GetPromptNode(node);

            if (childPromptNode != null)
            {
                result.Add(childPromptNode);
            }
        }

        return result.Count != 0;
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
