// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace ContentSafety.Services.PromptShield;

/// <summary>
/// Flags potential vulnerabilities within user input.
/// More information here: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-jailbreak#interpret-the-api-response
/// </summary>
public class PromptShieldAnalysis
{
    [JsonPropertyName("attackDetected")]
    public bool AttackDetected { get; set; }
}
