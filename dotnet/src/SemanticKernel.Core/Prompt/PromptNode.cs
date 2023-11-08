// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Prompt;

public class PromptNode
{
    private Dictionary<string, string>? _attributes;
    private List<PromptNode>? _childNodes;

    public string TagName { get; set; }

    public string? Content { get; set; }

    public Dictionary<string, string> Attributes
    {
        get => this._attributes ??= new();
        set => this._attributes = value;
    }

    public List<PromptNode> ChildNodes
    {
        get => this._childNodes ??= new();
        set => this._childNodes = value;
    }

    public PromptNode(string tagName)
    {
        this.TagName = tagName;
    }
}
