// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Content type to support message attachment.
/// </summary>
[Experimental("SKEXP0110")]
public class MessageAttachmentContent : FileReferenceContent
{
    /// <summary>
    /// The associated tool.
    /// </summary>
    public string Tool { get; init; } = string.Empty;

    /// <summary>
    /// Initializes a new instance of the <see cref="FileReferenceContent"/> class.
    /// </summary>
    [JsonConstructor]
    public MessageAttachmentContent()
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="FileReferenceContent"/> class.
    /// </summary>
    /// <param name="fileId">The identifier of the referenced file.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public MessageAttachmentContent(
        string fileId,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(fileId, modelId, innerContent, metadata)
    {
        // %%% TOOL TYPE
    }
}
