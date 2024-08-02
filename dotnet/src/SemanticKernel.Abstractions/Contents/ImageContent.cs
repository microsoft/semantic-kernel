// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents image content.
/// </summary>
public class ImageContent : BinaryContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    [JsonConstructor]
    public ImageContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of image.</param>
    public ImageContent(Uri uri) : base(uri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="dataUri">DataUri of the image</param>
    public ImageContent(string dataUri) : base(dataUri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ImageContent"/> class.
    /// </summary>
    /// <param name="data">Byte array of the image</param>
    /// <param name="mimeType">Mime type of the image</param>
    public ImageContent(ReadOnlyMemory<byte> data, string? mimeType) : base(data, mimeType)
    {
    }
}
