#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

internal sealed class GeminiResponse
{
    [JsonPropertyName("candidates")]
    public GeminiResponseCandidate[] Candidates { get; set; }

    [JsonPropertyName("promptFeedback")]
    public GeminiResponsePromptFeedback PromptFeedback { get; set; }
}

internal sealed class GeminiResponseCandidate
{
    [JsonPropertyName("content")]
    public GeminiResponseContent Content { get; set; }

    [JsonPropertyName("finishReason")]
    public string FinishReason { get; set; }

    [JsonPropertyName("index")]
    public int Index { get; set; }

    [JsonPropertyName("safetyRatings")]
    public GeminiResponseSafetyRating[] SafetyRatings { get; set; }

    [JsonPropertyName("tokenCount")]
    public int TokenCount { get; set; }
}

internal sealed class GeminiResponseContent
{
    [JsonPropertyName("parts")]
    public GeminiResponsePart[] Parts { get; set; }

    [JsonPropertyName("role")]
    public string Role { get; set; }
}

internal sealed class GeminiResponsePart
{
    [JsonPropertyName("text")]
    public string Text { get; set; }
}

internal sealed class GeminiResponseSafetyRating
{
    [JsonPropertyName("category")]
    public string Category { get; set; }

    [JsonPropertyName("probability")]
    public string Probability { get; set; }

    [JsonPropertyName("block")]
    public bool Block { get; set; }
}

internal sealed class GeminiResponsePromptFeedback
{
    [JsonPropertyName("blockReason")]
    public string BlockReason { get; set; }

    [JsonPropertyName("safetyRatings")]
    public GeminiResponseSafetyRating[] SafetyRatings { get; set; }
}
