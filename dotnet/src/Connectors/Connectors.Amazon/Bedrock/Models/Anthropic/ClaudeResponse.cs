// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Connectors.Amazon.Models.Anthropic;

public class ClaudeResponse
{
    [JsonPropertyName("completion")]
    public string Completion { get; set; }

    [JsonPropertyName("stop_reason")]
    public string StopReason { get; set; }

    [JsonPropertyName("stop")]
    public string Stop { get; set; }
}
