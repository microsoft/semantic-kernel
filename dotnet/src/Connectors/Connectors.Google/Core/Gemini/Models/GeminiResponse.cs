// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// Response from the model supporting multiple candidates.
/// </summary>
internal sealed class GeminiResponse
{
    /// <summary>
    /// Candidate responses from the model.
    /// </summary>
    [JsonPropertyName("candidates")]
    public IList<GeminiResponseCandidate>? Candidates { get; set; }

    /// <summary>
    /// Returns the prompt's feedback related to the content filters.
    /// </summary>
    [JsonPropertyName("promptFeedback")]
    public PromptFeedbackElement? PromptFeedback { get; set; }

    /// <summary>
    /// Returns the usage metadata for the request.
    /// </summary>
    [JsonPropertyName("usageMetadata")]
    public UsageMetadataElement? UsageMetadata { get; set; }

    /// <summary>
    /// Represents the usage metadata of a Gemini response.
    /// </summary>
    internal sealed class UsageMetadataElement
    {
        /// <summary>
        /// Gets the number of used tokens by prompt.
        /// </summary>
        [JsonPropertyName("promptTokenCount")]
        public int PromptTokenCount { get; set; }

        /// <summary>
        /// Gets the number of cached content tokens used.
        /// </summary>
        [JsonPropertyName("cachedContentTokenCount")]
        public int CachedContentTokenCount { get; set; }

        /// <summary>
        /// Gets the number of thoughts tokens used.
        /// </summary>
        [JsonPropertyName("thoughtsTokenCount")]
        public int ThoughtsTokenCount { get; set; }

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

    /// <summary>
    /// Feedback for the prompt.
    /// </summary>
    internal sealed class PromptFeedbackElement
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
}
