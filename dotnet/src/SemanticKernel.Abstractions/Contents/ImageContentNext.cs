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
    /// <param name="uri">The URI of image.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    public ImageContentNext(
        Uri uri,
        object? innerContent,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(uri, innerContent, modelId, metadata)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="byteArray">The Data used as DataUri for the image.</param>
    /// <param name="mimeType">The mime type of the image</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public ImageContentNext(
        ReadOnlyMemory<byte> byteArray,
        string mimeType,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(byteArray, mimeType, innerContent, modelId, metadata)
    {
    }
}
