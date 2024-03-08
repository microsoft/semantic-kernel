// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents an entry in the OpenAI classification result.
/// </summary>
public sealed class OpenAIClassificationEntry
{
    internal OpenAIClassificationEntry(OpenAIClassificationCategory category, bool flagged, double score)
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
    /// Gets a value indicating whether the category violates the OpenAI's policy.
    /// </summary>
    public bool Flagged { get; }

    /// <summary>
    /// Raw scores output by the model, denoting the model's confidence that the input violates the OpenAI's policy for the category.
    /// The value is between 0 and 1, where higher values denote higher confidence. The scores should not be interpreted as probabilities.
    /// </summary>
    public double Score { get; }

    /// <summary>
    /// Returns a string representation in record style of the OpenAIClassificationEntry object.
    /// </summary>
    public override string ToString()
        => $"{nameof(OpenAIClassificationEntry)} {{ Category = {this.Category}, Flagged = {this.Flagged}, Score = {this.Score} }}";
}
