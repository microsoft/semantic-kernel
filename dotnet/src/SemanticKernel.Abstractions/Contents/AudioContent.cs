// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable CA1054 // URI-like parameters should not be strings

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents audio content.
/// </summary>
public class AudioContent : BinaryContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AudioContent"/> class.
    /// </summary>
    [JsonConstructor]
    public AudioContent(string uri) : base(uri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AudioContent"/> class.
    /// </summary>
    /// <param name="data">The audio binary data.</param>
    /// <param name="mimeType">Audio mime type.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content,</param>
    /// <param name="metadata">Additional metadata</param>
    public AudioContent(
        ReadOnlyMemory<byte> data,
        string? mimeType,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(
            data: data,
            mimeType: mimeType,
            uri: null,
            innerContent,
            modelId,
            metadata)
    {
    }
}
