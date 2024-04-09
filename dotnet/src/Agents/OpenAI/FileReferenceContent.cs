// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Content type to support file references.
/// </summary>
public class FileReferenceContent : KernelContent
{
    /// <summary>
    /// The file identifier.
    /// </summary>
    public string? FileId { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FileReferenceContent"/> class.
    /// </summary>
    public FileReferenceContent()
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="FileReferenceContent"/> class.
    /// </summary>
    /// <param name="fileId">The identifier of the referenced file.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content,</param>
    /// <param name="metadata">Additional metadata</param>
    public FileReferenceContent(
        string fileId,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.FileId = fileId;
    }
}
