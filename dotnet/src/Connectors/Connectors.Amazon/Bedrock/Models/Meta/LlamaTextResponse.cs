// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Connectors.Amazon.Models.Meta;

public class LlamaTextResponse
{
    [JsonPropertyName("generation")]
    public string Generation { get; set; }

    [JsonPropertyName("prompt_token_count")]
    public int PromptTokenCount { get; set; }

    [JsonPropertyName("generation_token_count")]
    public int GenerationTokenCount { get; set; }

    [JsonPropertyName("stop_reason")]
    public string StopReason { get; set; }
}
