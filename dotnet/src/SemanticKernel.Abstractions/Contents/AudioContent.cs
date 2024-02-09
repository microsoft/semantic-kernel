// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.TextToAudio;

namespace Microsoft.SemanticKernel.Contents;

/// <summary>
/// Represents audio content return from a <see cref="ITextToAudioService" /> service.
/// </summary>
[Experimental("SKEXP0005")]
public class AudioContent : KernelContent
{
    /// <summary>
    /// The audio binary data.
    /// </summary>
    public BinaryData? AudioData { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AudioContent"/> class.
    /// </summary>
    /// <param name="audioData">The audio binary data.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content,</param>
    /// <param name="metadata">Additional metadata</param>
    public AudioContent(
        BinaryData audioData,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.AudioData = audioData;
    }
}
