// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Content type to support file references.
/// </summary>
[Experimental("SKEXP0110")]
public class StreamingFileReferenceContent : StreamingKernelContent
{
    /// <summary>
    /// The file identifier.
    /// </summary>
    public string FileId { get; init; } = string.Empty;

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingFileReferenceContent"/> class.
    /// </summary>
    [JsonConstructor]
    public StreamingFileReferenceContent()
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingFileReferenceContent"/> class.
    /// </summary>
    /// <param name="fileId">The identifier of the referenced file.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public StreamingFileReferenceContent(
        string fileId,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, choiceIndex: 0, modelId, metadata)
    {
        this.FileId = fileId;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.FileId;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.ToString());
    }
}
