// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace ContentSafety.Services.PromptShield;

public class PromptShieldResponse
{
    [JsonPropertyName("userPromptAnalysis")]
    public PromptShieldAnalysis? UserPromptAnalysis { get; set; }

    [JsonPropertyName("documentsAnalysis")]
    public List<PromptShieldAnalysis>? DocumentsAnalysis { get; set; }
}
