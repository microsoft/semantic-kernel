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
    /// The image binary data.
    /// </summary>
    public BinaryData? Data { get; }

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
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Uri = uri;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="data">The Data used as DataUri for the image.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Additional metadata</param>
    public ImageContent(
        BinaryData data,
        string? modelId = null,
        object? innerContent = null,
        Encoding? encoding = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        Verify.NotNull(data, nameof(data));

        if (data!.IsEmpty)
        {
            throw new ArgumentException("Data cannot be empty", nameof(data));
        }

        if (string.IsNullOrWhiteSpace(data!.MediaType))
        {
            throw new ArgumentException("MediaType is needed for DataUri Images", nameof(data));
        }

        this.Data = data;
    }

    /// <summary>
    /// Returns the string representation of the image.
    /// BinaryData images will be represented as DataUri
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
        if (this.Data is null)
        {
            return null;
        }

        return $"data:{this.Data.MediaType};base64,{Convert.ToBase64String(this.Data.ToArray())}";
    }
}
