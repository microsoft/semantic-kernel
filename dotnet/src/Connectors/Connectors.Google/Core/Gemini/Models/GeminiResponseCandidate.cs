// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// A response candidate generated from the model.
/// </summary>
internal sealed class GeminiResponseCandidate
{
    /// <summary>
    /// Generated content returned from the model.
    /// </summary>
    [JsonPropertyName("content")]
    public GeminiContent? Content { get; set; }

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
    public IList<GeminiSafetyRating>? SafetyRatings { get; set; }

    /// <summary>
    /// Token count for this candidate.
    /// </summary>
    [JsonPropertyName("tokenCount")]
    public int TokenCount { get; set; }
}
