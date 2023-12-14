// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class that contains information about node in prompt.
/// </summary>
internal class PromptNode
{
    private Dictionary<string, string>? _attributes;
    private List<PromptNode>? _childNodes;

    /// <summary>
    /// Node tag name.
    /// </summary>
    public string TagName { get; set; }

    /// <summary>
    /// Node content.
    /// </summary>
    public string? Content { get; set; }

    /// <summary>
    /// Collection of node attributes.
    /// </summary>
    public Dictionary<string, string> Attributes
    {
        get => this._attributes ??= new();
        set => this._attributes = value;
    }

    /// <summary>
    /// Collection of child nodes.
    /// </summary>
    public List<PromptNode> ChildNodes
    {
        get => this._childNodes ??= new();
        set => this._childNodes = value;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptNode"/> class.
    /// </summary>
    /// <param name="tagName">Node tag name.</param>
    public PromptNode(string tagName)
    {
        this.TagName = tagName;
    }
}
