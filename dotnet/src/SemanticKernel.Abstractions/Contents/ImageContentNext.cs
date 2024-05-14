// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable CA1054 // URI-like parameters should not be strings

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents image content.
/// </summary>
public sealed class ImageContentNext : BinaryContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    [JsonConstructor]
    public ImageContentNext(string uri)
        : base(uri, null, null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="dataUri">DataUri of the image.</param>
    /// <param name="mimeType">MimeType of the image</param>
    /// <param name="uri">The referenced Uri of the image.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    public ImageContentNext(
        string? dataUri = null,
        string? mimeType = null,
        Uri? uri = null,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(
            dataUri,
            mimeType,
            uri,
            innerContent,
            modelId,
            metadata)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="byteArray">The Data used as DataUri for the image.</param>
    /// <param name="mimeType">The mime type of the image</param>
    /// <param name="uri">The referenced Uri of the image.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public ImageContentNext(
        ReadOnlyMemory<byte> byteArray,
        string mimeType,
        Uri? uri = null,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(byteArray, mimeType, uri, innerContent, modelId, metadata)
    {
    }
}
