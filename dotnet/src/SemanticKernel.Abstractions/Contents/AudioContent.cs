// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;

namespace Microsoft.SemanticKernel.Contents;

/// <summary>
/// Represents audio content.
/// </summary>
[Experimental("SKEXP0005")]
public class AudioContent : KernelContent
{
    /// <summary>
    /// The audio binary data.
    /// </summary>
    /// <remarks>
    /// If both <see cref="Data"/> and <see cref="Stream"/> are provided,
    /// <see cref="Data"/> takes precedence over <see cref="Stream"/>.
    /// </remarks>
    public BinaryData? Data { get; set; }

    /// <summary>
    /// The audio stream.
    /// </summary>
    /// <remarks>
    /// If both <see cref="Data"/> and <see cref="Stream"/> are provided,
    /// <see cref="Data"/> takes precedence over <see cref="Stream"/>.
    /// </remarks>
    public Stream? Stream { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AudioContent"/> class.
    /// </summary>
    /// <param name="data">The audio binary data.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content,</param>
    /// <param name="metadata">Additional metadata</param>
    public AudioContent(
        BinaryData data,
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
    /// <param name="stream">The audio stream.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content,</param>
    /// <param name="metadata">Additional metadata</param>
    public AudioContent(
        Stream stream,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Stream = stream;
    }
}
