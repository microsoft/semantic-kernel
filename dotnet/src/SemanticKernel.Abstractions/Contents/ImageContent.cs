// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents image content.
/// </summary>
public sealed class ImageContent : KernelContent
{
    /// <summary>
    /// The URI of image.
    /// </summary>
    public Uri? Uri { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of image.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Additional metadata</param>
    public ImageContent(
        Uri uri,
        string? modelId = null,
        object? innerContent = null,
        Encoding? encoding = null,
        IDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Uri = uri;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Uri?.ToString() ?? string.Empty;
    }
}
