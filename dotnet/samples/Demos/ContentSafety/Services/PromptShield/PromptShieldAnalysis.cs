// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace ContentSafety.Services.PromptShield;

public class PromptShieldAnalysis
{
    [JsonPropertyName("attackDetected")]
    public bool AttackDetected { get; set; }
}
