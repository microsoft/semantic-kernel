// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents reasoning content.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class ReasoningContent : KernelContent
{
    private string? _text;

    /// <summary>
    /// The reasoning content.
    /// </summary>
    [AllowNull]
    public string Text
    {
        get => this._text ?? string.Empty;
        init => this._text = value;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ReasoningContent"/> class.
    /// </summary>
    /// <param name="text">Text reasoning content</param>
    [JsonConstructor]
    public ReasoningContent(string? text = null)
    {
        this._text = text;
    }

    /// <inheritdoc/>
    public override string ToString() => this.Text;
}
