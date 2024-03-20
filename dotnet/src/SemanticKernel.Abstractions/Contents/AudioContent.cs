// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents audio content.
/// </summary>
[Experimental("SKEXP0001")]
public class AudioContent : KernelContent
{
    /// <summary>
    /// URI of audio file.
    /// </summary>
    public Uri? Uri { get; set; }

    /// <summary>
    /// The audio data.
    /// </summary>
    public ReadOnlyMemory<byte>? Data { get; set; }

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
    /// <param name="data">The audio binary data.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content,</param>
    /// <param name="metadata">Additional metadata</param>
    public AudioContent(
        ReadOnlyMemory<byte> data,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Data = data;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AudioContent"/> class.
    /// </summary>
    /// <param name="uri">URI of audio file.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content,</param>
    /// <param name="metadata">Additional metadata</param>
    public AudioContent(
        Uri uri,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Uri = uri;
    }
}
