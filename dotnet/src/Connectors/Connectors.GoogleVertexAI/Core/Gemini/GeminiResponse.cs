// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini;

/// <summary>
/// Response from the model supporting multiple candidates.
/// </summary>
public sealed class GeminiResponse
{
    /// <summary>
    /// Candidate responses from the model.
    /// </summary>
    [JsonPropertyName("candidates")]
    public IList<GeminiResponseCandidate> Candidates { get; set; } = null!;

    /// <summary>
    /// Returns the prompt's feedback related to the content filters.
    /// </summary>
    [JsonPropertyName("promptFeedback")]
    public GeminiResponsePromptFeedback? PromptFeedback { get; set; }

    /// <summary>
    /// Returns the usage metadata for the request.
    /// </summary>
    [JsonPropertyName("usageMetadata")]
    public GeminiResponseUsageMetadata? UsageMetadata { get; set; }
}

/// <summary>
/// A response candidate generated from the model.
/// </summary>
public sealed class GeminiResponseCandidate
{
    /// <summary>
    /// Generated content returned from the model.
    /// </summary>
    [JsonPropertyName("content")]
    public GeminiResponseContent Content { get; set; } = null!;

    /// <summary>
    /// Optional. The reason why the model stopped generating tokens.
    /// </summary>
    /// <remarks>
    /// If empty, the model has not stopped generating the tokens.
    /// </remarks>
    [JsonPropertyName("finishReason")]
    public GeminiFinishReason FinishReason { get; set; }

    /// <summary>
    /// Index of the candidate in the list of candidates.
    /// </summary>
    [JsonPropertyName("index")]
    public int Index { get; set; }

    /// <summary>
    /// List of ratings for the safety of a response candidate.
    /// </summary>
    /// <remarks>
    /// There is at most one rating per category.
    /// </remarks>
    [JsonPropertyName("safetyRatings")]
    public IList<GeminiSafetyRating> SafetyRatings { get; set; } = null!;

    /// <summary>
    /// Token count for this candidate.
    /// </summary>
    [JsonPropertyName("tokenCount")]
    public int TokenCount { get; set; }
}

/// <summary>
/// The base structured datatype containing multi-part content of a message.
/// </summary>
public sealed class GeminiResponseContent
{
    /// <summary>
    /// Ordered Parts that constitute a single message. Parts may have different MIME types.
    /// </summary>
    [JsonPropertyName("parts")]
    public IList<GeminiPart> Parts { get; set; } = null!;

    /// <summary>
    /// Optional. The producer of the content. Must be either 'user' or 'model'.
    /// </summary>
    /// <remarks>Useful to set for multi-turn conversations, otherwise can be left blank or unset.</remarks>
    [JsonPropertyName("role")]
    [JsonConverter(typeof(AuthorRoleConverter))]
    public AuthorRole? Role { get; set; }
}

/// <summary>
/// Feedback for the prompt.
/// </summary>
public sealed class GeminiResponsePromptFeedback
{
    /// <summary>
    /// Optional. If set, the prompt was blocked and no candidates are returned. Rephrase your prompt.
    /// </summary>
    [JsonPropertyName("blockReason")]
    public string? BlockReason { get; set; }

    /// <summary>
    /// Ratings for safety of the prompt. There is at most one rating per category.
    /// </summary>
    [JsonPropertyName("safetyRatings")]
    public IList<GeminiSafetyRating> SafetyRatings { get; set; } = null!;
}

/// <summary>
/// Represents the usage metadata of a Gemini response.
/// </summary>
public sealed class GeminiResponseUsageMetadata
{
    /// <summary>
    /// Gets the number of used tokens by prompt.
    /// </summary>
    [JsonPropertyName("promptTokenCount")]
    public int PromptTokenCount { get; set; }

    /// <summary>
    /// Gets the count of used tokens for all candidates.
    /// </summary>
    [JsonPropertyName("candidatesTokenCount")]
    public int CandidatesTokenCount { get; set; }

    /// <summary>
    /// Gets the total number of used tokens.
    /// </summary>
    [JsonPropertyName("totalTokenCount")]
    public int TotalTokenCount { get; set; }
}
