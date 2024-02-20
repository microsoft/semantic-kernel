// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents the response received from the OpenAI Moderation API.
/// </summary>
public sealed class OpenAIModerationResponse
{
    /// <summary>
    /// The unique identifier for the moderation request.
    /// </summary>
    [JsonPropertyName("id")]
    [JsonRequired]
    public string Id { get; set; } = null!;

    /// <summary>
    /// The model used to generate the moderation results.
    /// </summary>
    [JsonPropertyName("model")]
    [JsonRequired]
    public string ModelId { get; set; } = null!;

    /// <summary>
    /// A list of moderation objects.
    /// </summary>
    [JsonPropertyName("results")]
    [JsonRequired]
    public IList<ModerationResult> Results { get; set; } = null!;

    /// <summary>
    /// Represents a moderation result obtained from the OpenAI Moderation API.
    /// </summary>
    public sealed class ModerationResult
    {
        /// <summary>
        /// Whether the content violates OpenAI's usage policies.
        /// </summary>
        [JsonRequired]
        [JsonPropertyName("flagged")]
        public bool Flagged { get; set; }

        /// <summary>
        /// A list of the categories, and whether they are flagged or not.
        /// </summary>
        [JsonPropertyName("categories")]
        [JsonRequired]
        public IDictionary<string, bool> CategoryFlags { get; set; } = null!;

        /// <summary>
        /// A list of the categories along with their scores as predicted by model.
        /// </summary>
        [JsonPropertyName("category_scores")]
        [JsonRequired]
        public IDictionary<string, double> CategoryScores { get; set; } = null!;
    }
}
