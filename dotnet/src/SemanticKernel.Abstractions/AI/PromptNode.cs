// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class that contains information about node in prompt.
/// </summary>
internal sealed class PromptNode(string tagName)
{
    private Dictionary<string, string>? _attributes;
    private List<PromptNode>? _childNodes;

    /// <summary>
    /// Node tag name.
    /// </summary>
    public string TagName { get; set; } = tagName;

    /// <summary>
    /// Node content.
    /// </summary>
    public string? Content { get; set; }

    /// <summary>
    /// Collection of node attributes.
    /// </summary>
    public Dictionary<string, string> Attributes
    {
        get => this._attributes ??= [];
        set => this._attributes = value;
    }

    /// <summary>
    /// Collection of child nodes.
    /// </summary>
    public List<PromptNode> ChildNodes
    {
        get => this._childNodes ??= [];
        set => this._childNodes = value;
    }
}
