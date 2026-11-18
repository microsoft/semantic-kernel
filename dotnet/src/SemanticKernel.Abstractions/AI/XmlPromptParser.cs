// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Web;
using System.Xml;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class to parse text prompt from XML format.
/// </summary>
internal static class XmlPromptParser
{
    /// <summary>
    /// Maximum element nesting depth supported in an XML prompt, where top-level prompt elements are at depth 1.
    /// </summary>
    /// <remarks>
    /// Chat prompts only need a shallow structure, such as message elements that contain content elements.
    /// Each <see cref="PromptNode"/> stores the serialized content of its whole subtree, so the parsing work
    /// grows with the nesting depth multiplied by the prompt size. Limiting the depth keeps that work
    /// proportional to the prompt size and also bounds the recursion in <see cref="GetPromptNode"/>.
    /// </remarks>
    internal const int MaxElementDepth = 64;

    /// <summary>
    /// Parses text prompt and sets output as collection of <see cref="PromptNode"/> instances.
    /// </summary>
    /// <param name="prompt">Text prompt to parse.</param>
    /// <param name="result">Parsing output as collection of <see cref="PromptNode"/> instances.</param>
    /// <returns>
    /// Returns true if parsing was successful, otherwise false. Prompts whose elements are nested deeper than
    /// <see cref="MaxElementDepth"/> are not parsed.
    /// </returns>
    public static bool TryParse(string prompt, [NotNullWhen(true)] out List<PromptNode>? result)
    {
        result = null;

        // The below parsing is _very_ expensive, especially when the content is not valid XML and an
        // exception is thrown. Try to avoid it in the common case where the prompt is obviously not XML.
        // To be valid XML, at a minimum:
        // - the string would need to be non-null
        // - it would need to contain the start of a tag
        // - it would need to contain a closing tag, which could include either </ or />
        int startPos;
        if (prompt is null ||
#pragma warning disable CA1307 // Specify StringComparison for clarity
            (startPos = prompt.IndexOf('<')) < 0 ||
#pragma warning restore CA1307
            (prompt.IndexOf("</", startPos + 1, StringComparison.Ordinal) < 0 &&
             prompt.IndexOf("/>", startPos + 1, StringComparison.Ordinal) < 0))
        {
            return false;
        }

        var xmlDocument = new XmlDocument()
        {
            // This is necessary to preserve whitespace within prompts as this may be significant.
            // E.g. if the prompt contains well formatted code and we want the LLM to return well formatted code.
            PreserveWhitespace = true
        };

        try
        {
            xmlDocument.LoadXml($"<root>{prompt}</root>");
        }
        catch (XmlException)
        {
            return false;
        }

        // Check the depth before building prompt nodes, because building them serializes every subtree.
        // A rejected prompt takes the same path as invalid XML, so callers use it as plain text.
        if (ExceedsMaxElementDepth(xmlDocument.DocumentElement!))
        {
            return false;
        }

        foreach (XmlNode node in xmlDocument.DocumentElement!.ChildNodes)
        {
            if (GetPromptNode(node) is { } childPromptNode)
            {
                (result ??= []).Add(childPromptNode);
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

        // Since we're preserving whitespace for the contents within each XMLNode, we
        // need to skip any whitespace nodes at the front of the children.
        var firstNonWhitespaceChild = node.ChildNodes
            .Cast<XmlNode>()
            .FirstOrDefault(n => n.NodeType != XmlNodeType.Whitespace);

        var isCData = firstNonWhitespaceChild?.NodeType == XmlNodeType.CDATA;
        var nodeContent = isCData
            ? node.InnerText.Trim()
            : node.InnerXml.Trim();

        var promptNode = new PromptNode(node.Name)
        {
            Content = !string.IsNullOrEmpty(nodeContent) ? HttpUtility.HtmlDecode(nodeContent) : null
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

            if (childPromptNode is not null)
            {
                promptNode.ChildNodes.Add(childPromptNode);
            }
        }

        return promptNode;
    }

    /// <summary>
    /// Checks whether any element below <paramref name="root"/> is nested deeper than <see cref="MaxElementDepth"/>.
    /// </summary>
    /// <param name="root">The wrapper element that contains the top-level prompt elements.</param>
    private static bool ExceedsMaxElementDepth(XmlElement root)
    {
        // Walk the tree without recursion so that a deeply nested document cannot exhaust the stack here.
        var depth = 1;
        var node = root.FirstChild;

        while (node is not null)
        {
            if (node.NodeType == XmlNodeType.Element)
            {
                if (depth > MaxElementDepth)
                {
                    return true;
                }

                if (node.FirstChild is { } firstChild)
                {
                    node = firstChild;
                    depth++;
                    continue;
                }
            }

            // Move to the next sibling, climbing back up through parents that have no further siblings.
            while (node.NextSibling is null)
            {
                node = node.ParentNode!;
                if (--depth == 0)
                {
                    // Climbing to depth 0 means the walk has returned to the root element.
                    return false;
                }
            }

            node = node.NextSibling;
        }

        return false;
    }
}
