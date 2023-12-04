// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

/// <summary>
/// StreamResponse class in <see href="https://github.com/huggingface/text-generation-inference/tree/main/clients/python"></see>
/// </summary>
public class StreamingTextContent : StreamingContent
{
    /// <inheritdoc/>
    public override int ChoiceIndex { get; }

    /// <summary>
    /// Text associated to the update
    /// </summary>
    public string Content { get; }

    /// <summary>
    /// Create a new instance of the <see cref="StreamingTextContent"/> class.
    /// </summary>
    /// <param name="text">Text update</param>
    /// <param name="resultIndex">Index of the choice</param>
    /// <param name="innerContentObject">Inner chunk object</param>
    /// <param name="metadata">Metadata information</param>
    public StreamingTextContent(string text, int resultIndex, object? innerContentObject = null, Dictionary<string, object>? metadata = null) : base(innerContentObject, metadata)
    {
        this.ChoiceIndex = resultIndex;
        this.Content = text;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.ToString());
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Content;
    }
}
