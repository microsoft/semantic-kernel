// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Reflection;
using System.Runtime.Serialization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Pod type of the index, see https://docs.pinecone.io/docs/indexes#pods-pod-types-and-pod-sizes.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
[JsonConverter(typeof(PodTypeJsonConverter))]
public enum PodType
{
    /// <summary>
    /// Represents an undefined or uninitialized PodType.
    /// </summary>
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
    P2X8 = 12,

    /// <summary>
    /// Enum Starter for value: starter
    /// </summary>
    [EnumMember(Value = "starter")]
    Starter = 13,

    /// <summary>
    /// Enum Nano for value: nano
    /// </summary>
    [EnumMember(Value = "nano")]
    Nano = 14
}

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class PodTypeJsonConverter : JsonConverter<PodType>
#pragma warning restore CA1812
{
    public override PodType Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? stringValue = reader.GetString();

        object? enumValue = Enum
            .GetValues(typeToConvert)
            .Cast<object?>()
            .FirstOrDefault(value => value is not null && typeToConvert.GetMember(value.ToString()!)[0]
                .GetCustomAttribute<EnumMemberAttribute>() is { } enumMemberAttr && enumMemberAttr.Value == stringValue);

        if (enumValue is not null)
        {
            return (PodType)enumValue;
        }

        throw new JsonException($"Unable to parse '{stringValue}' as a PodType enum.");
    }

    public override void Write(Utf8JsonWriter writer, PodType value, JsonSerializerOptions options)
    {
        if (value.GetType().GetMember(value.ToString())[0].GetCustomAttribute<EnumMemberAttribute>() is not { } enumMemberAttr)
        {
            throw new JsonException($"Unable to find EnumMember attribute for PodType '{value}'.");
        }

        writer.WriteStringValue(enumMemberAttr.Value);
    }
}
