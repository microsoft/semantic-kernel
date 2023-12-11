// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Abstraction of text content chunks when using streaming from <see cref="ITextGenerationService"/> interface.
/// </summary>
public class StreamingTextContent : StreamingKernelContent
{
    /// <summary>
    /// Text associated to the update
    /// </summary>
    public string? Text { get; }

    /// <summary>
    /// The encoding of the text content.
    /// </summary>
    [JsonIgnore]
    public Encoding Encoding { get; set; }

    /// <summary>
    /// Create a new instance of the <see cref="StreamingTextContent"/> class.
    /// </summary>
    /// <param name="text">Text update</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner chunk object</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Metadata information</param>
    [JsonConstructor]
    public StreamingTextContent(string? text, int choiceIndex = 0, string? modelId = null, object? innerContent = null, Encoding? encoding = null, IDictionary<string, object?>? metadata = null) : base(innerContent, choiceIndex, modelId, metadata)
    {
        this.Text = text;
        this.Encoding = encoding ?? Encoding.UTF8;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Text ?? string.Empty;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return this.Encoding.GetBytes(this.ToString());
    }
}
