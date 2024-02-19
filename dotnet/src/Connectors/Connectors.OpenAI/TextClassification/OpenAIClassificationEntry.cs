// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents an entry in the OpenAI classification result.
/// </summary>
public sealed class OpenAIClassificationEntry
{
    internal OpenAIClassificationEntry(bool flagged, double score, OpenAIClassificationCategory category)
    {
        this.Flagged = flagged;
        this.Score = score;
        this.Category = category;
    }

    /// <summary>
    /// Represents a category for the OpenAI classification result.
    /// </summary>
    public OpenAIClassificationCategory Category { get; }

    /// <summary>
    /// Gets a value indicating whether the category is flagged.
    /// </summary>
    public bool Flagged { get; }

    /// <summary>
    /// Represents a score for the OpenAI classification result.
    /// </summary>
    public double Score { get; }

    /// <inheritdoc />
    public override string ToString() => $"ClassificationEntry {{ Category = {this.Category}, Score = {this.Score}, Flagged = {this.Flagged} }}";
}
