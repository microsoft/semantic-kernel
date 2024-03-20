// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents audio content.
/// </summary>
[Experimental("SKEXP0005")]
public class AudioStreamContent : KernelContent
{
    /// <summary>
    /// The stream of the audio data.
    /// AudioStreamContent will not dispose the stream for you.
    /// </summary>
    public Stream Stream { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelContent"/> class.
    /// </summary>
    /// <param name="stream">The stream of the audio data. AudioStreamContent will not dispose the stream for you.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Metadata associated with the content</param>
    public AudioStreamContent(Stream stream, string? modelId = null, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(stream, modelId, metadata)
    {
        this.Stream = stream;
    }
}
