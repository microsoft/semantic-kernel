// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace ContentSafety.Services.PromptShield;

/// <summary>
/// Input for Prompt Shield service.
/// More information here: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-jailbreak#analyze-attacks
/// </summary>
public class PromptShieldRequest
{
    /// <summary>
    /// Represents a text or message input provided by the user. This could be a question, command, or other form of text input.
    /// </summary>
    [JsonPropertyName("userPrompt")]
    public string UserPrompt { get; set; } = string.Empty;

    /// <summary>
    /// Represents a list or collection of textual documents, articles, or other string-based content.
    /// </summary>
    [JsonPropertyName("documents")]
    public List<string>? Documents { get; set; } = [];
}
