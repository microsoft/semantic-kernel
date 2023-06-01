// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.Serialization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// Pod type of the index, see https://docs.pinecone.io/docs/indexes#pods-pod-types-and-pod-sizes.
/// </summary>
[JsonConverter(typeof(PodTypeJsonConverter))]
public enum PodType
{
    None = 0,

    /// <summary>
    /// Enum S1X1 for value: s1.x1
    /// </summary>
    [EnumMember(Value = "s1.x1")]
    S1X1 = 1,

    /// <summary>
    /// Enum S1X2 for value: s1.x2
    /// </summary>
    [EnumMember(Value = "s1.x2")]
    S1X2 = 2,

    /// <summary>
    /// Enum S1X4 for value: s1.x4
    /// </summary>
    [EnumMember(Value = "s1.x4")]
    S1X4 = 3,

    /// <summary>
    /// Enum S1X8 for value: s1.x8
    /// </summary>
    [EnumMember(Value = "s1.x8")]
    S1X8 = 4,

    /// <summary>
    /// Enum P1X1 for value: p1.x1
    /// </summary>
    [EnumMember(Value = "p1.x1")]
    P1X1 = 5,

    /// <summary>
    /// Enum P1X2 for value: p1.x2
    /// </summary>
    [EnumMember(Value = "p1.x2")]
    P1X2 = 6,

    /// <summary>
    /// Enum P1X4 for value: p1.x4
    /// </summary>
    [EnumMember(Value = "p1.x4")]
    P1X4 = 7,

    /// <summary>
    /// Enum P1X8 for value: p1.x8
    /// </summary>
    [EnumMember(Value = "p1.x8")]
    P1X8 = 8,

    /// <summary>
    /// Enum P2X1 for value: p2.x1
    /// </summary>
    [EnumMember(Value = "p2.x1")]
    P2X1 = 9,

    /// <summary>
    /// Enum P2X2 for value: p2.x2
    /// </summary>
    [EnumMember(Value = "p2.x2")]
    P2X2 = 10,

    /// <summary>
    /// Enum P2X4 for value: p2.x4
    /// </summary>
    [EnumMember(Value = "p2.x4")]
    P2X4 = 11,

    /// <summary>
    /// Enum P2X8 for value: p2.x8
    /// </summary>
    [EnumMember(Value = "p2.x8")]
    P2X8 = 12
}

internal sealed class PodTypeJsonConverter : JsonConverter<PodType>
{
    public override PodType Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? stringValue = reader.GetString();
        return stringValue switch
        {
            "s1.x1" => PodType.S1X1,
            "s1.x2" => PodType.S1X2,
            "s1.x4" => PodType.S1X4,
            "s1.x8" => PodType.S1X8,
            "p1.x1" => PodType.P1X1,
            "p1.x2" => PodType.P1X2,
            "p1.x4" => PodType.P1X4,
            "p1.x8" => PodType.P1X8,
            "p2.x1" => PodType.P2X1,
            "p2.x2" => PodType.P2X2,
            "p2.x4" => PodType.P2X4,
            "p2.x8" => PodType.P2X8,
            _ => throw new JsonException($"Unable to parse '{stringValue}'"),
        };
    }

    public override void Write(Utf8JsonWriter writer, PodType value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value switch
        {
            PodType.S1X1 => "s1.x1",
            PodType.S1X2 => "s1.x2",
            PodType.S1X4 => "s1.x4",
            PodType.S1X8 => "s1.x8",
            PodType.P1X1 => "p1.x1",
            PodType.P1X2 => "p1.x2",
            PodType.P1X4 => "p1.x4",
            PodType.P1X8 => "p1.x8",
            PodType.P2X1 => "p2.x1",
            PodType.P2X2 => "p2.x2",
            PodType.P2X4 => "p2.x4",
            PodType.P2X8 => "p2.x8",
            _ => throw new JsonException($"Unable to find value '{value}'."),
        });
    }
}
