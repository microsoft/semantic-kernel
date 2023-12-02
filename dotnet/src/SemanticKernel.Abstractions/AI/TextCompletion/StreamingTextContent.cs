// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

/// <summary>
/// Streaming text result update.
/// </summary>
public abstract class StreamingTextContent : StreamingContent
{
    /// <summary>
    /// Text associated to the update
    /// </summary>
    public string Content { get; }

    /// <summary>
    /// Create a new instance of the <see cref="StreamingTextContent"/> class.
    /// </summary>
    /// <param name="text">Text update</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="innerContentObject">Inner chunk object</param>
    /// <param name="metadata">Metadata information</param>
    protected StreamingTextContent(string text, int choiceIndex = 0, object? innerContentObject = null, Dictionary<string, object>? metadata = null) : base(innerContentObject, choiceIndex, metadata)
    {
        this.Content = text;
    }
}
