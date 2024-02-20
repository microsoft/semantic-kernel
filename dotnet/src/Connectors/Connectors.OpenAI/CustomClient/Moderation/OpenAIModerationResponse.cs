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
    [JsonRequired]
    public string Id { get; set; } = null!;

    /// <summary>
    /// The model used to generate the moderation results.
    /// </summary>
    [JsonRequired]
    public string ModelId { get; set; } = null!;

    /// <summary>
    /// A list of moderation objects.
    /// </summary>
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
        public bool Flagged { get; set; }

        /// <summary>
        /// A list of the categories, and whether they are flagged or not.
        /// </summary>
        [JsonRequired]
        public IList<ModerationCategoryFlag> CategoryFlags { get; set; } = null!;

        /// <summary>
        /// A list of the categories along with their scores as predicted by model.
        /// </summary>
        [JsonRequired]
        public IList<ModerationCategoryScore> CategoryScores { get; set; } = null!;
    }

    /// <summary>
    /// Represents a moderation flag for a category.
    /// </summary>
    public sealed class ModerationCategoryFlag
    {
        /// <summary>
        /// The category of the moderation result.
        /// </summary>
        [JsonRequired]
        public string Label { get; set; } = null!;

        /// <summary>
        /// Gets or sets a value indicating whether the content has been flagged.
        /// </summary>
        [JsonRequired]
        public bool Flagged { get; set; }
    }

    /// <summary>
    /// Represents a category score obtained from moderation results.
    /// </summary>
    public sealed class ModerationCategoryScore
    {
        /// <summary>
        /// The category of the moderation result.
        /// </summary>
        [JsonRequired]
        public string Label { get; set; } = null!;

        /// <summary>
        /// The confidence of the moderation result.
        /// </summary>
        [JsonRequired]
        public double Score { get; set; }
    }
}
