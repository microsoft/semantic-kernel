// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents a Claude Finish Reason.
/// </summary>
[JsonConverter(typeof(ClaudeFinishReasonConverter))]
public readonly struct ClaudeFinishReason : IEquatable<ClaudeFinishReason>
{
    /// <summary>
    /// Natural stop point of the model or provided stop sequence.
    /// </summary>
    public static ClaudeFinishReason Stop { get; } = new("end_turn");

    /// <summary>
    /// The maximum number of tokens as specified in the request was reached.
    /// </summary>
    public static ClaudeFinishReason MaxTokens { get; } = new("max_tokens");

    /// <summary>
    /// One of your provided custom stop sequences was generated.
    /// </summary>
    public static ClaudeFinishReason StopSequence { get; } = new("stop_sequence");

    /// <summary>
    /// Gets the label of the property.
    /// Label is used for serialization.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Represents a Claude Finish Reason.
    /// </summary>
    [JsonConstructor]
    public ClaudeFinishReason(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label;
    }

    /// <summary>
    /// Represents the equality operator for comparing two instances of <see cref="ClaudeFinishReason"/>.
    /// </summary>
    /// <param name="left">The left <see cref="ClaudeFinishReason"/> instance to compare.</param>
    /// <param name="right">The right <see cref="ClaudeFinishReason"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are equal; otherwise, <c>false</c>.</returns>
    public static bool operator ==(ClaudeFinishReason left, ClaudeFinishReason right)
        => left.Equals(right);

    /// <summary>
    /// Represents the inequality operator for comparing two instances of <see cref="ClaudeFinishReason"/>.
    /// </summary>
    /// <param name="left">The left <see cref="ClaudeFinishReason"/> instance to compare.</param>
    /// <param name="right">The right <see cref="ClaudeFinishReason"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are not equal; otherwise, <c>false</c>.</returns>
    public static bool operator !=(ClaudeFinishReason left, ClaudeFinishReason right)
        => !(left == right);

    /// <inheritdoc />
    public bool Equals(ClaudeFinishReason other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc />
    public override bool Equals(object? obj)
        => obj is ClaudeFinishReason other && this == other;

    /// <inheritdoc />
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label ?? string.Empty);

    /// <inheritdoc />
    public override string ToString() => this.Label ?? string.Empty;
}

internal sealed class ClaudeFinishReasonConverter : JsonConverter<ClaudeFinishReason>
{
    public override ClaudeFinishReason Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString()!);

    public override void Write(Utf8JsonWriter writer, ClaudeFinishReason value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Label);
}
