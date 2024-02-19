// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents a category for the OpenAI classification result.
/// </summary>
[JsonConverter(typeof(OpenAIClassificationCategoryConverter))]
public readonly struct OpenAIClassificationCategory : IEquatable<OpenAIClassificationCategory>
{
    /// <summary>
    /// Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion,
    /// nationality, sexual orientation, disability status, or caste. Hateful content aimed
    /// at non-protected groups (e.g., chess players) is harassment.
    /// </summary>
    public static OpenAIClassificationCategory Hate { get; } = new("hate");

    /// <summary>
    /// Hateful content that also includes violence or serious harm towards the targeted group based on race,
    /// gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.
    /// </summary>
    public static OpenAIClassificationCategory HateAndThreatening { get; } = new("hate/threatening");

    /// <summary>
    /// Content that expresses, incites, or promotes harassing language towards any target.
    /// </summary>
    public static OpenAIClassificationCategory Harassment { get; } = new("harassment");

    /// <summary>
    /// Harassment content that also includes violence or serious harm towards any target.
    /// </summary>
    public static OpenAIClassificationCategory HarassmentAndThreatening { get; } = new("harassment/threatening");

    /// <summary>
    /// Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.
    /// </summary>
    public static OpenAIClassificationCategory SelfHarm { get; } = new("self-harm");

    /// <summary>
    /// Content where the speaker expresses that they are engaging or intend to engage
    /// in acts of self-harm, such as suicide, cutting, and eating disorders.
    /// </summary>
    public static OpenAIClassificationCategory SelfHarmIntent { get; } = new("self-harm/intent");

    /// <summary>
    /// Content that encourages performing acts of self-harm, such as suicide, cutting,
    /// and eating disorders, or that gives instructions or advice on how to commit such acts.
    /// </summary>
    public static OpenAIClassificationCategory SelfHarmInstruction { get; } = new("self-harm/instructions");

    /// <summary>
    /// Content meant to arouse sexual excitement, such as the description of sexual activity,
    /// or that promotes sexual services (excluding sex education and wellness).
    /// </summary>
    public static OpenAIClassificationCategory Sexual { get; } = new("sexual");

    /// <summary>
    /// Sexual content that includes an individual who is under 18 years old.
    /// </summary>
    public static OpenAIClassificationCategory SexualMinors { get; } = new("sexual/minors");

    /// <summary>
    /// Content that depicts death, violence, or physical injury.
    /// </summary>
    public static OpenAIClassificationCategory Violence { get; } = new("violence");

    /// <summary>
    /// Content that depicts death, violence, or physical injury in graphic detail.
    /// </summary>
    public static OpenAIClassificationCategory ViolenceOnGraphic { get; } = new("violence/graphic");

    /// <summary>
    /// Gets the label of the property.
    /// Label is used for serialization.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIClassificationCategory"/> struct.
    /// </summary>
    [JsonConstructor]
    public OpenAIClassificationCategory(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label;
    }

    /// <summary>
    /// An enumerable collection of OpenAIClassificationCategory.
    /// </summary>
    public static IEnumerable<OpenAIClassificationCategory> GetAll() =>
        typeof(OpenAIClassificationCategory).GetFields(BindingFlags.Public |
                                                       BindingFlags.Static |
                                                       BindingFlags.DeclaredOnly)
            .Select(f => f.GetValue(null))
            .Cast<OpenAIClassificationCategory>();

    /// <summary>
    /// Represents the equality operator for comparing two instances of <see cref="OpenAIClassificationCategory"/>.
    /// </summary>
    /// <param name="left">The left <see cref="OpenAIClassificationCategory"/> instance to compare.</param>
    /// <param name="right">The right <see cref="OpenAIClassificationCategory"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are equal; otherwise, <c>false</c>.</returns>
    public static bool operator ==(OpenAIClassificationCategory left, OpenAIClassificationCategory right)
        => left.Equals(right);

    /// <summary>
    /// Represents the inequality operator for comparing two instances of <see cref="OpenAIClassificationCategory"/>.
    /// </summary>
    /// <param name="left">The left <see cref="OpenAIClassificationCategory"/> instance to compare.</param>
    /// <param name="right">The right <see cref="OpenAIClassificationCategory"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are not equal; otherwise, <c>false</c>.</returns>
    public static bool operator !=(OpenAIClassificationCategory left, OpenAIClassificationCategory right)
        => !(left == right);

    /// <inheritdoc />
    public bool Equals(OpenAIClassificationCategory other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc />
    public override bool Equals(object? obj)
        => obj is OpenAIClassificationCategory other && this == other;

    /// <inheritdoc />
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label ?? string.Empty);

    /// <inheritdoc />
    public override string ToString() => this.Label ?? string.Empty;
}

internal sealed class OpenAIClassificationCategoryConverter : JsonConverter<OpenAIClassificationCategory>
{
    public override OpenAIClassificationCategory Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString()!);

    public override void Write(Utf8JsonWriter writer, OpenAIClassificationCategory value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Label);
}
