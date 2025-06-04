// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Connectors.Onnx.UnitTests;

internal sealed class CustomPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Temperature to sample with.
    /// </summary>
    [JsonPropertyName("temperature")]
    public float? Temperature { get; set; }
}
