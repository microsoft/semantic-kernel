// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

/// <summary>
/// Streaming text result update.
/// </summary>
public class StreamingTextResultChunk : StreamingResultChunk
{
    /// <inheritdoc/>
    public override string Type => "huggingface_text_update";

    /// <inheritdoc/>
    public override int ChoiceIndex { get; }

    /// <summary>
    /// Text associated to the update
    /// </summary>
    public string Content { get; }

    /// <summary>
    /// Create a new instance of the <see cref="StreamingTextResultChunk"/> class.
    /// </summary>
    /// <param name="text">Text update</param>
    /// <param name="choiceIndex">Index of the choice</param>
    public StreamingTextResultChunk(string text, int choiceIndex)
    {
        this.ChoiceIndex = choiceIndex;
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
