// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace ContentSafety.Services.PromptShield;

public class PromptShieldRequest
{
    [JsonPropertyName("userPrompt")]
    public string UserPrompt { get; set; } = string.Empty;

    [JsonPropertyName("documents")]
    public List<string> Documents { get; set; } = [];
}
