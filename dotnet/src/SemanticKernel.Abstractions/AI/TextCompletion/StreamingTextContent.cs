// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

/// <summary>
/// Streaming text result update.
/// </summary>
public class StreamingTextContent : StreamingContent
{
    /// <summary>
    /// Text associated to the update
    /// </summary>
    public string? Text { get; }

    /// <summary>
    /// Create a new instance of the <see cref="StreamingTextContent"/> class.
    /// </summary>
    /// <param name="text">Text update</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="innerContentObject">Inner chunk object</param>
    /// <param name="metadata">Metadata information</param>
    public StreamingTextContent(string? text, int choiceIndex = 0, object? innerContentObject = null, Dictionary<string, object>? metadata = null) : base(innerContentObject, choiceIndex, metadata)
    {
        this.Text = text;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Text ?? string.Empty;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.Text);
    }
}
