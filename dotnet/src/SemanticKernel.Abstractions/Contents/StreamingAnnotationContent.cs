// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Content type to support message annotations.
/// </summary>
[Experimental("SKEXP0110")]
public class StreamingAnnotationContent : StreamingKernelContent
{
    /// <summary>
    /// The file identifier.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? FileId { get; init; }

    /// <summary>
    /// The citation.
    /// </summary>
    public string Quote { get; init; } = string.Empty;

    /// <summary>
    /// Start index of the citation.
    /// </summary>
    public int StartIndex { get; init; }

    /// <summary>
    /// End index of the citation.
    /// </summary>
    public int EndIndex { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingAnnotationContent"/> class.
    /// </summary>
    [JsonConstructor]
    public StreamingAnnotationContent()
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingAnnotationContent"/> class.
    /// </summary>
    /// <param name="quote">The source text being referenced.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public StreamingAnnotationContent(
        string quote,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, choiceIndex: 0, modelId, metadata)
    {
        this.Quote = quote;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        bool hasFileId = !string.IsNullOrEmpty(this.FileId);

        if (hasFileId)
        {
            return $"{this.Quote}: {this.FileId}";
        }

        return this.Quote;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.ToString());
    }
}
