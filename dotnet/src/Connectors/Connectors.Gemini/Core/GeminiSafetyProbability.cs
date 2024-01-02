#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

/// <summary>
/// Represents a Gemini Safety Probability.
/// </summary>
public readonly struct GeminiSafetyProbability : IEquatable<GeminiSafetyProbability>
{
    /// <summary>
    /// Probability is unspecified.
    /// </summary>
    public static GeminiSafetyProbability Unspecified { get; } = new("HARM_PROBABILITY_UNSPECIFIED");

    /// <summary>
    /// Content has a negligible chance of being unsafe.
    /// </summary>
    public static GeminiSafetyProbability Negligible { get; } = new("NEGLIGIBLE");

    /// <summary>
    /// Content has a low chance of being unsafe.
    /// </summary>
    public static GeminiSafetyProbability Low { get; } = new("LOW");

    /// <summary>
    /// Content has a medium chance of being unsafe.
    /// </summary>
    public static GeminiSafetyProbability Medium { get; } = new("MEDIUM");

    /// <summary>
    /// Content has a high chance of being unsafe.
    /// </summary>
    public static GeminiSafetyProbability High { get; } = new("HIGH");

    /// <summary>
    /// Gets the label of the property.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Represents a Gemini Safety Probability.
    /// </summary>
    [JsonConstructor]
    public GeminiSafetyProbability(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label;
    }

    /// <summary>
    /// Represents the equality operator for comparing two instances of <see cref="GeminiSafetyProbability"/>.
    /// </summary>
    /// <param name="left">The left <see cref="GeminiSafetyProbability"/> instance to compare.</param>
    /// <param name="right">The right <see cref="GeminiSafetyProbability"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are equal; otherwise, <c>false</c>.</returns>
    public static bool operator ==(GeminiSafetyProbability left, GeminiSafetyProbability right)
        => left.Equals(right);

    /// <summary>
    /// Represents the inequality operator for comparing two instances of <see cref="GeminiSafetyProbability"/>.
    /// </summary>
    /// <param name="left">The left <see cref="GeminiSafetyProbability"/> instance to compare.</param>
    /// <param name="right">The right <see cref="GeminiSafetyProbability"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are not equal; otherwise, <c>false</c>.</returns>
    public static bool operator !=(GeminiSafetyProbability left, GeminiSafetyProbability right)
        => !(left == right);

    /// <inheritdoc />
    public bool Equals(GeminiSafetyProbability other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc />
    public override bool Equals(object? obj)
        => obj is GeminiSafetyProbability other && this == other;

    /// <inheritdoc />
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label ?? string.Empty);

    /// <inheritdoc />
    public override string ToString() => this.Label ?? string.Empty;
}
