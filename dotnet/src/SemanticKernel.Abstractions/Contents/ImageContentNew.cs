// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable CA1054 // URI-like parameters should not be strings

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents image content.
/// </summary>
public sealed class ImageContentV2 : BinaryContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    [JsonConstructor]
    public ImageContentV2(string uriData)
        : base(uriData, null, null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of image.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public ImageContentV2(Uri uri) : this(uri.ToString())
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
    public ImageContentV2(
        ReadOnlyMemory<byte> byteArray,
        string mimeType,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(byteArray, mimeType, innerContent, modelId, metadata)
    {
    }

    /// <summary>
    /// Returns the string representation of the image.
    /// In-memory images will be represented as DataUri
    /// Remote Uri images will be represented as is
    /// </summary>
    /// <remarks>
    /// When Data is provided it takes precedence over URI
    /// </remarks>
    public override string ToString()
    {
        return this.BuildDataUri() ?? this.Uri?.ToString() ?? string.Empty;
    }

    private string? BuildDataUri()
    {
        if (this.Data is null || string.IsNullOrEmpty(this.MimeType))
        {
            return null;
        }

        return $"data:{this.MimeType};base64,{Convert.ToBase64String(this.Data.Value.ToArray())}";
    }
}
