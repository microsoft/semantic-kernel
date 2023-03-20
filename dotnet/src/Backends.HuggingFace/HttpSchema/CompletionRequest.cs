// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Backends.HuggingFace.HttpSchema;

[Serializable]
public sealed class CompletionRequest
{
    [JsonPropertyName("prompt")]
    public string? Prompt { get; set; }

    [JsonPropertyName("model")]
    public string? Model { get; set; }
}
