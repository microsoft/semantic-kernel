// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents action content.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class ActionContent : KernelContent
{
    private string _text;

    /// <summary>
    /// The action content.
    /// </summary>
    public string Text
    {
        get => this._text;
        init
        {
            Verify.NotNull(value, nameof(this.Text));
            this._text = value;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ActionContent"/> class.
    /// </summary>
    /// <param name="text">The action text</param>
    [JsonConstructor]
    public ActionContent(string text)
    {
        Verify.NotNullOrWhiteSpace(text, nameof(text));

        this._text = text;
    }

    /// <inheritdoc/>
    public override string ToString() => this.Text;
}
