// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents a safety rating for a Gemini.
/// </summary>
public sealed class GeminiSafetyRating
{
    /// <summary>
    /// Was this content blocked because of this rating?
    /// </summary>
    [JsonPropertyName("block")]
    public bool Block { get; set; }

    /// <summary>
    /// The category for this rating.
    /// </summary>
    [JsonPropertyName("category")]
    public GeminiSafetyCategory Category { get; set; }

    /// <summary>
    /// The probability of harm for this content.
    /// </summary>
    [JsonPropertyName("probability")]
    public GeminiSafetyProbability Probability { get; set; }
}

/// <summary>
/// Represents a Gemini Safety Probability.
/// </summary>
[JsonConverter(typeof(GeminiSafetyProbabilityConverter))]
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
    /// Label is used for serialization.
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

internal sealed class GeminiSafetyProbabilityConverter : JsonConverter<GeminiSafetyProbability>
{
    public override GeminiSafetyProbability Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString()!);

    public override void Write(Utf8JsonWriter writer, GeminiSafetyProbability value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Label);
}
