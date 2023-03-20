// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Backends.HuggingFace.HttpSchema;

[Serializable]
public sealed class EmbeddingRequest
{
    [JsonPropertyName("input")]
    public IList<string>? Input { get; set; }

    [JsonPropertyName("model")]
    public string? Model { get; set; }
}
