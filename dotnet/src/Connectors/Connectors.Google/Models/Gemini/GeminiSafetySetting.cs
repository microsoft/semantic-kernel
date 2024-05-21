// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents a safety setting for the Gemini prompt.
/// </summary>
public sealed class GeminiSafetySetting
{
    /// <summary>
    /// Initializes a new instance of the Gemini <see cref="GeminiSafetySetting"/> class.
    /// </summary>
    /// <param name="category">Category of safety</param>
    /// <param name="threshold">Value</param>
    [JsonConstructor]
    public GeminiSafetySetting(GeminiSafetyCategory category, GeminiSafetyThreshold threshold)
    {
        this.Category = category;
        this.Threshold = threshold;
    }

    /// <summary>
    /// Initializes a new instance of the Gemini <see cref="GeminiSafetySetting"/> class by cloning another instance.
    /// </summary>
    /// <param name="other">Instance to clone</param>
    public GeminiSafetySetting(GeminiSafetySetting other)
    {
        this.Category = other.Category;
        this.Threshold = other.Threshold;
    }

    /// <summary>
    /// Gets or sets the safety category.
    /// </summary>
    [JsonPropertyName("category")]
    public GeminiSafetyCategory Category { get; set; }

    /// <summary>
    /// Gets or sets the safety threshold.
    /// </summary>
    [JsonPropertyName("threshold")]
    public GeminiSafetyThreshold Threshold { get; set; }
}

/// <summary>
/// Represents a safety category in the Gemini system.
/// </summary>
[JsonConverter(typeof(GeminiSafetyCategoryConverter))]
public readonly struct GeminiSafetyCategory : IEquatable<GeminiSafetyCategory>
{
    /// <summary>
    /// Category is unspecified.
    /// </summary>
    public static GeminiSafetyCategory Unspecified { get; } = new("HARM_CATEGORY_UNSPECIFIED");

    /// <summary>
    /// Contains negative or harmful comments targeting identity and/or protected attributes.
    /// </summary>
    public static GeminiSafetyCategory Derogatory { get; } = new("HARM_CATEGORY_DEROGATORY");

    /// <summary>
    /// Includes content that is rude, disrespectful, or profane.
    /// </summary>
    public static GeminiSafetyCategory Toxicity { get; } = new("HARM_CATEGORY_TOXICITY");

    /// <summary>
    /// Describes scenarios depicting violence against an individual or group, or general descriptions of gore.
    /// </summary>
    public static GeminiSafetyCategory Violence { get; } = new("HARM_CATEGORY_VIOLENCE");

    /// <summary>
    /// Contains references to sexual acts or other lewd content.
    /// </summary>
    public static GeminiSafetyCategory Sexual { get; } = new("HARM_CATEGORY_SEXUAL");

    /// <summary>
    /// Contains unchecked medical advice.
    /// </summary>
    public static GeminiSafetyCategory Medical { get; } = new("HARM_CATEGORY_MEDICAL");

    /// <summary>
    /// Includes content that promotes, facilitates, or encourages harmful acts.
    /// </summary>
    public static GeminiSafetyCategory Dangerous { get; } = new("HARM_CATEGORY_DANGEROUS");

    /// <summary>
    /// Consists of harassment content.
    /// </summary>
    public static GeminiSafetyCategory Harassment { get; } = new("HARM_CATEGORY_HARASSMENT");

    /// <summary>
    /// Contains sexually explicit content.
    /// </summary>
    public static GeminiSafetyCategory SexuallyExplicit { get; } = new("HARM_CATEGORY_SEXUALLY_EXPLICIT");

    /// <summary>
    /// Contains dangerous content.
    /// </summary>
    public static GeminiSafetyCategory DangerousContent { get; } = new("HARM_CATEGORY_DANGEROUS_CONTENT");

    /// <summary>
    /// Gets the label of the property.
    /// Label will be serialized.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Represents a Gemini Safety Category.
    /// </summary>
    [JsonConstructor]
    public GeminiSafetyCategory(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label;
    }

    /// <summary>
    /// Represents the equality operator for comparing two instances of <see cref="GeminiSafetyCategory"/>.
    /// </summary>
    /// <param name="left">The left <see cref="GeminiSafetyCategory"/> instance to compare.</param>
    /// <param name="right">The right <see cref="GeminiSafetyCategory"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are equal; otherwise, <c>false</c>.</returns>
    public static bool operator ==(GeminiSafetyCategory left, GeminiSafetyCategory right)
        => left.Equals(right);

    /// <summary>
    /// Represents the inequality operator for comparing two instances of <see cref="GeminiSafetyCategory"/>.
    /// </summary>
    /// <param name="left">The left <see cref="GeminiSafetyCategory"/> instance to compare.</param>
    /// <param name="right">The right <see cref="GeminiSafetyCategory"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are not equal; otherwise, <c>false</c>.</returns>
    public static bool operator !=(GeminiSafetyCategory left, GeminiSafetyCategory right)
        => !(left == right);

    /// <inheritdoc />
    public bool Equals(GeminiSafetyCategory other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc />
    public override bool Equals(object? obj)
        => obj is GeminiSafetyCategory other && this == other;

    /// <inheritdoc />
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label ?? string.Empty);

    /// <inheritdoc />
    public override string ToString() => this.Label ?? string.Empty;
}

/// <summary>
/// Represents a safety threshold for Gemini.
/// </summary>
[JsonConverter(typeof(GeminiSafetyThresholdConverter))]
public readonly struct GeminiSafetyThreshold : IEquatable<GeminiSafetyThreshold>
{
    /// <summary>
    /// Always show regardless of probability of unsafe content.
    /// </summary>
    public static GeminiSafetyThreshold BlockNone { get; } = new("BLOCK_NONE");

    /// <summary>
    /// Block when high probability of unsafe content.
    /// </summary>
    public static GeminiSafetyThreshold BlockOnlyHigh { get; } = new("BLOCK_ONLY_HIGH");

    /// <summary>
    /// Block when medium or high probability of unsafe content.
    /// </summary>
    public static GeminiSafetyThreshold BlockMediumAndAbove { get; } = new("BLOCK_MEDIUM_AND_ABOVE");

    /// <summary>
    /// Block when low, medium or high probability of unsafe content.
    /// </summary>
    public static GeminiSafetyThreshold BlockLowAndAbove { get; } = new("BLOCK_LOW_AND_ABOVE");

    /// <summary>
    /// Threshold is unspecified, block using default threshold.
    /// </summary>
    public static GeminiSafetyThreshold Unspecified { get; } = new("HARM_BLOCK_THRESHOLD_UNSPECIFIED");

    /// <summary>
    /// Gets the label.
    /// Label will be serialized.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Creates a Gemini safety threshold instance.
    /// </summary>
    [JsonConstructor]
    public GeminiSafetyThreshold(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label;
    }

    /// <summary>
    /// Determines whether two GeminiSafetyThreshold objects are equal.
    /// </summary>
    /// <param name="left">The first GeminiSafetyThreshold object to compare.</param>
    /// <param name="right">The second GeminiSafetyThreshold object to compare.</param>
    /// <returns>True if the objects are equal, false otherwise.</returns>
    public static bool operator ==(GeminiSafetyThreshold left, GeminiSafetyThreshold right)
        => left.Equals(right);

    /// <summary>
    /// Determines whether two instances of GeminiSafetyThreshold are not equal.
    /// </summary>
    /// <param name="left">The first GeminiSafetyThreshold to compare.</param>
    /// <param name="right">The second GeminiSafetyThreshold to compare.</param>
    /// <returns>true if the two instances are not equal; otherwise, false.</returns>
    public static bool operator !=(GeminiSafetyThreshold left, GeminiSafetyThreshold right)
        => !(left == right);

    /// <inheritdoc />
    public bool Equals(GeminiSafetyThreshold other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc />
    public override bool Equals(object? obj)
        => obj is GeminiSafetyThreshold other && this == other;

    /// <inheritdoc />
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label ?? string.Empty);

    /// <inheritdoc />
    public override string ToString() => this.Label ?? string.Empty;
}

internal sealed class GeminiSafetyCategoryConverter : JsonConverter<GeminiSafetyCategory>
{
    public override GeminiSafetyCategory Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString()!);

    public override void Write(Utf8JsonWriter writer, GeminiSafetyCategory value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Label);
}

internal sealed class GeminiSafetyThresholdConverter : JsonConverter<GeminiSafetyThreshold>
{
    public override GeminiSafetyThreshold Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString()!);

    public override void Write(Utf8JsonWriter writer, GeminiSafetyThreshold value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Label);
}
