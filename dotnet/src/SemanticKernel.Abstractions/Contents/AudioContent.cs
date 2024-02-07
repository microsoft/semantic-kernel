// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Contents;

public sealed class AudioContent : KernelContent
{
    public BinaryData Audio { get; set; }

    public AudioContent(BinaryData audio, object? innerContent, string? modelId = null, IReadOnlyDictionary<string, object?>? metadata = null) : base(innerContent, modelId, metadata)
    {
        this.Audio = audio;
    }
}
