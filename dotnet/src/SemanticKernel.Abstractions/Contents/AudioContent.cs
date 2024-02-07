// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;

namespace Microsoft.SemanticKernel.Contents;

public sealed class AudioContent : KernelContent
{
    public BinaryData AudioData { get; set; }

    public AudioContent(BinaryData audioData, string? modelId = null, object? innerContent = null, Encoding? encoding = null, IReadOnlyDictionary<string, object?>? metadata = null) : base(innerContent, modelId, metadata)
    {
        this.AudioData = audioData;
    }
}
