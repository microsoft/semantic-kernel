#region HEADER
// Copyright (c) Microsoft. All rights reserved.
#endregion

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

internal sealed class TextGenerationResponse
{
    [JsonPropertyName("candidates")]
    public TextGenerationResponseCandidates[] Candidates { get; set; }

    [JsonPropertyName("promptFeedback")]
    public TextGenerationResponsePromptFeedback PromptFeedback { get; set; }
}

internal sealed class TextGenerationResponseCandidates
{
    [JsonPropertyName("content")]
    public TextGenerationResponseContent Content { get; set; }

    [JsonPropertyName("finishReason")]
    public string FinishReason { get; set; }

    [JsonPropertyName("index")]
    public int Index { get; set; }

    [JsonPropertyName("safetyRatings")]
    public TextGenerationResponseSafetyRatings[] SafetyRatings { get; set; }
}

internal sealed class TextGenerationResponseContent
{
    [JsonPropertyName("parts")]
    public TextGenerationResponseParts[] Parts { get; set; }

    [JsonPropertyName("role")]
    public string Role { get; set; }
}

internal sealed class TextGenerationResponseParts
{
    [JsonPropertyName("text")]
    public string Text { get; set; }
}

internal sealed class TextGenerationResponseSafetyRatings
{
    [JsonPropertyName("category")]
    public string Category { get; set; }

    [JsonPropertyName("probability")]
    public string Probability { get; set; }
}

internal sealed class TextGenerationResponsePromptFeedback
{
    [JsonPropertyName("safetyRatings")]
    public TextGenerationResponseSafetyRatings[] SafetyRatings { get; set; }
}
