// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

/// <summary>
/// Represents a text content result.
/// </summary>
public sealed class TextContent : ModelContent
{
    /// <summary>
    /// The text content.
    /// </summary>
    public string Text { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TextContent"/> class.
    /// </summary>
    /// <param name="text">Text content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public TextContent(string text, object? innerContent = null, Dictionary<string, object>? metadata = null) : base(innerContent, metadata)
    {
        this.Text = text;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Text ?? string.Empty;
    }
}
