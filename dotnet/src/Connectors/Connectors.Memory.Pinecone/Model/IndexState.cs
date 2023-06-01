// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.Serialization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// The current status of a index.
/// </summary>
[JsonConverter(typeof(IndexStateJsonConverter))]
public enum IndexState
{
    /// <summary>
    /// Default value.
    /// </summary>
    None = 0,

    /// <summary>
    /// Enum Initializing for value: Initializing
    /// </summary>
    [EnumMember(Value = "Initializing")]
    Initializing = 1,

    /// <summary>
    /// Enum ScalingUp for value: ScalingUp
    /// </summary>
    [EnumMember(Value = "ScalingUp")]
    ScalingUp = 2,

    /// <summary>
    /// Enum ScalingDown for value: ScalingDown
    /// </summary>
    [EnumMember(Value = "ScalingDown")]
    ScalingDown = 3,

    /// <summary>
    /// Enum Terminating for value: Terminating
    /// </summary>
    [EnumMember(Value = "Terminating")]
    Terminating = 4,

    /// <summary>
    /// Enum Ready for value: Ready
    /// </summary>
    [EnumMember(Value = "Ready")]
    Ready = 5,
}

// TODO https://github.com/dotnet/runtime/issues/79311
internal sealed class IndexStateJsonConverter : JsonConverter<IndexState>
{
    public override IndexState Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? stringValue = reader.GetString();
        return
            nameof(IndexState.Initializing).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? IndexState.Initializing :
            nameof(IndexState.ScalingUp).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? IndexState.ScalingUp :
            nameof(IndexState.ScalingDown).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? IndexState.ScalingDown :
            nameof(IndexState.Terminating).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? IndexState.Terminating :
            nameof(IndexState.Ready).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? IndexState.Ready :
            throw new JsonException($"Unable to parse '{stringValue}'");
    }

    public override void Write(Utf8JsonWriter writer, IndexState value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value switch
        {
            IndexState.Initializing => nameof(IndexState.Initializing),
            IndexState.ScalingUp => nameof(IndexState.ScalingUp),
            IndexState.ScalingDown => nameof(IndexState.ScalingDown),
            IndexState.Terminating => nameof(IndexState.Terminating),
            IndexState.Ready => nameof(IndexState.Ready),
            _ => throw new JsonException($"Unable to find value '{value}'."),
        });
    }
}
