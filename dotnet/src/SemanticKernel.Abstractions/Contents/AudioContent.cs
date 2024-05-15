// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
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
    public AudioContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AudioContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of the referenced audio content.</param>
    /// <param name="mimeType">The MIME type of the audio content.</param>
    /// <param name="innerContent">The inner content of the audio content.</param>
    /// <param name="modelId">The model ID used to generate the audio content.</param>
    /// <param name="metadata">The metadata associated with the audio content.</param>
    public AudioContent(
        Uri? uri,
        string? mimeType = null,
        object? innerContent = null,
        string? modelId = null,
        ReadOnlyDictionary<string, object?>? metadata = null) : base((string?)null, uri, innerContent, modelId, metadata)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AudioContent"/> class.
    /// </summary>
    /// <param name="data">The audio binary data.</param>
    /// <param name="mimeType">The MIME type of the audio content.</param>
    /// <param name="innerContent">The inner content of the audio content.</param>
    /// <param name="modelId">The model ID used to generate the audio content.</param>
    /// <param name="metadata">The metadata associated with the audio content.</param>
    public AudioContent(
        ReadOnlyMemory<byte> data,
        string? mimeType,
        object? innerContent = null,
        string? modelId = null,
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
