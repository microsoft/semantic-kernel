// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace ContentSafety.Services.PromptShield;

/// <summary>
/// Flags potential vulnerabilities within user input.
/// More information here: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-jailbreak#interpret-the-api-response
/// </summary>
public class PromptShieldAnalysis
{
    /// <summary>
    /// Indicates whether a User Prompt attack (for example, malicious input, security threat) has been detected in the user prompt or
    /// a Document attack (for example, commands, malicious input) has been detected in the document.
    /// </summary>
    [JsonPropertyName("attackDetected")]
    public bool AttackDetected { get; set; }
}
