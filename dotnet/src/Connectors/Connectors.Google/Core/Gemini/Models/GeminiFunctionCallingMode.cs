// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// Represents a Gemini Function Calling Mode.
/// </summary>
[JsonConverter(typeof(GeminiFunctionCallingModeConverter))]
public readonly struct GeminiFunctionCallingMode : IEquatable<GeminiFunctionCallingMode>
{
    /// <summary>
    /// The default model behavior. The model decides to predict either a function call or a natural language response.
    /// </summary>
    public static GeminiFunctionCallingMode Default { get; } = new("AUTO");

    /// <summary>
    /// The model is constrained to always predict a function call. If allowed_function_names is not provided,
    /// the model picks from all of the available function declarations.
    /// If allowed_function_names is provided, the model picks from the set of allowed functions.
    /// </summary>
    public static GeminiFunctionCallingMode Any { get; } = new("ANY");

    /// <summary>
    /// The model won't predict a function call. In this case, the model behavior is the same as if you don't pass any function declarations.
    /// </summary>
    public static GeminiFunctionCallingMode None { get; } = new("NONE");

    /// <summary>
    /// Gets the label of the property.
    /// Label is used for serialization.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Represents a Gemini Function Calling Mode.
    /// </summary>
    [JsonConstructor]
    public GeminiFunctionCallingMode(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label;
    }

    /// <summary>
    /// Represents the equality operator for comparing two instances of <see cref="GeminiFunctionCallingMode"/>.
    /// </summary>
    /// <param name="left">The left <see cref="GeminiFunctionCallingMode"/> instance to compare.</param>
    /// <param name="right">The right <see cref="GeminiFunctionCallingMode"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are equal; otherwise, <c>false</c>.</returns>
    public static bool operator ==(GeminiFunctionCallingMode left, GeminiFunctionCallingMode right)
        => left.Equals(right);

    /// <summary>
    /// Represents the inequality operator for comparing two instances of <see cref="GeminiFunctionCallingMode"/>.
    /// </summary>
    /// <param name="left">The left <see cref="GeminiFunctionCallingMode"/> instance to compare.</param>
    /// <param name="right">The right <see cref="GeminiFunctionCallingMode"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are not equal; otherwise, <c>false</c>.</returns>
    public static bool operator !=(GeminiFunctionCallingMode left, GeminiFunctionCallingMode right)
        => !(left == right);

    /// <inheritdoc />
    public bool Equals(GeminiFunctionCallingMode other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc />
    public override bool Equals(object? obj)
        => obj is GeminiFunctionCallingMode other && this == other;

    /// <inheritdoc />
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label ?? string.Empty);

    /// <inheritdoc />
    public override string ToString() => this.Label ?? string.Empty;
}

internal sealed class GeminiFunctionCallingModeConverter : JsonConverter<GeminiFunctionCallingMode>
{
    public override GeminiFunctionCallingMode Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString()!);

    public override void Write(Utf8JsonWriter writer, GeminiFunctionCallingMode value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Label);
}
