// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents a Anthropic Finish Reason.
/// </summary>
[JsonConverter(typeof(AnthropicFinishReasonConverter))]
public readonly struct AnthropicFinishReason : IEquatable<AnthropicFinishReason>
{
    /// <summary>
    /// Natural stop point of the model or provided stop sequence.
    /// </summary>
    public static AnthropicFinishReason Stop { get; } = new("end_turn");

    /// <summary>
    /// The maximum number of tokens as specified in the request was reached.
    /// </summary>
    public static AnthropicFinishReason MaxTokens { get; } = new("max_tokens");

    /// <summary>
    /// One of your provided custom stop sequences was generated.
    /// </summary>
    public static AnthropicFinishReason StopSequence { get; } = new("stop_sequence");

    /// <summary>
    /// The model invoked one or more tools
    /// </summary>
    public static AnthropicFinishReason ToolUse { get; } = new("tool_use");

    /// <summary>
    /// Gets the label of the property.
    /// Label is used for serialization.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Represents a Anthropic Finish Reason.
    /// </summary>
    [JsonConstructor]
    public AnthropicFinishReason(string label)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        this.Label = label;
    }

    /// <summary>
    /// Represents the equality operator for comparing two instances of <see cref="AnthropicFinishReason"/>.
    /// </summary>
    /// <param name="left">The left <see cref="AnthropicFinishReason"/> instance to compare.</param>
    /// <param name="right">The right <see cref="AnthropicFinishReason"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are equal; otherwise, <c>false</c>.</returns>
    public static bool operator ==(AnthropicFinishReason left, AnthropicFinishReason right)
        => left.Equals(right);

    /// <summary>
    /// Represents the inequality operator for comparing two instances of <see cref="AnthropicFinishReason"/>.
    /// </summary>
    /// <param name="left">The left <see cref="AnthropicFinishReason"/> instance to compare.</param>
    /// <param name="right">The right <see cref="AnthropicFinishReason"/> instance to compare.</param>
    /// <returns><c>true</c> if the two instances are not equal; otherwise, <c>false</c>.</returns>
    public static bool operator !=(AnthropicFinishReason left, AnthropicFinishReason right)
        => !(left == right);

    /// <inheritdoc />
    public bool Equals(AnthropicFinishReason other)
        => string.Equals(this.Label, other.Label, StringComparison.OrdinalIgnoreCase);

    /// <inheritdoc />
    public override bool Equals(object? obj)
        => obj is AnthropicFinishReason other && this == other;

    /// <inheritdoc />
    public override int GetHashCode()
        => StringComparer.OrdinalIgnoreCase.GetHashCode(this.Label ?? string.Empty);

    /// <inheritdoc />
    public override string ToString() => this.Label ?? string.Empty;
}

internal sealed class AnthropicFinishReasonConverter : JsonConverter<AnthropicFinishReason>
{
    public override AnthropicFinishReason Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        => new(reader.GetString()!);

    public override void Write(Utf8JsonWriter writer, AnthropicFinishReason value, JsonSerializerOptions options)
        => writer.WriteStringValue(value.Label);
}
