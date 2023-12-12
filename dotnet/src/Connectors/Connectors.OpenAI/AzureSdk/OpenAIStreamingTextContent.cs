// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI and OpenAI Specialized streaming text content.
/// </summary>
/// <remarks>
/// Represents a text content chunk that was streamed from the remote model.
/// </remarks>
public sealed class OpenAIStreamingTextContent : StreamingTextContent
{
    /// <summary>
    /// Create a new instance of the <see cref="OpenAIStreamingTextContent"/> class.
    /// </summary>
    /// <param name="text">Text update</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContentObject">Inner chunk object</param>
    /// <param name="metadata">Metadata information</param>
    internal OpenAIStreamingTextContent(
        string text,
        int choiceIndex,
        string modelId,
        object? innerContentObject = null,
        Dictionary<string, object?>? metadata = null)
        : base(
            text,
            choiceIndex,
            modelId,
            innerContentObject,
            Encoding.UTF8,
            metadata)
    {
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return this.Encoding.GetBytes(this.ToString());
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Text ?? string.Empty;
    }
}
