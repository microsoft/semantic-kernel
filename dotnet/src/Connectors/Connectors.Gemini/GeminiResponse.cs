#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Text.Json.Serialization;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

public class GeminiResponse
{
    [JsonPropertyName("candidates")]
    public IList<GeminiResponseCandidate> Candidates { get; set; }

    [JsonPropertyName("promptFeedback")]
    public GeminiResponsePromptFeedback? PromptFeedback { get; set; }
}

public class GeminiResponseCandidate
{
    [JsonPropertyName("content")]
    public GeminiResponseContent Content { get; set; }

    [JsonPropertyName("finishReason")]
    public string FinishReason { get; set; }

    [JsonPropertyName("index")]
    public int Index { get; set; }

    [JsonPropertyName("safetyRatings")]
    public IList<GeminiResponseSafetyRating> SafetyRatings { get; set; }

    [JsonPropertyName("tokenCount")]
    public int TokenCount { get; set; }
}

public class GeminiResponseContent
{
    [JsonPropertyName("parts")]
    public IList<GeminiResponsePart> Parts { get; set; }

    [JsonPropertyName("role")]
    public string Role { get; set; }
}

public class GeminiResponsePart
{
    [JsonPropertyName("text")]
    public string Text { get; set; }
}

public class GeminiResponseSafetyRating
{
    [JsonPropertyName("category")]
    public string Category { get; set; }

    [JsonPropertyName("probability")]
    public string Probability { get; set; }

    [JsonPropertyName("block")]
    public bool Block { get; set; }
}

public class GeminiResponsePromptFeedback
{
    [JsonPropertyName("blockReason")]
    public string? BlockReason { get; set; }

    [JsonPropertyName("safetyRatings")]
    public IList<GeminiResponseSafetyRating> SafetyRatings { get; set; }
}
