// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Reflection;
using System.Runtime.Serialization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// The current status of a index.
/// </summary>
/// <value>The current status of a index.</value>
[JsonConverter(typeof(IndexStateJsonConverter))]
public enum IndexState
{

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

    NotInitialized
}

public class IndexStateJsonConverter : JsonConverter<IndexState>
{
    public override IndexState Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? stringValue = reader.GetString();

        foreach (object? enumValue in from object? enumValue in Enum.GetValues(typeToConvert)
                                      let enumMemberAttr =
                                          typeToConvert.GetMember(enumValue.ToString())[0].GetCustomAttribute(typeof(EnumMemberAttribute)) as
                                              EnumMemberAttribute
                                      where enumMemberAttr != null && enumMemberAttr.Value == stringValue
                                      select enumValue)
        {
            return (IndexState)enumValue;
        }
        throw new JsonException($"Unable to parse '{stringValue}' as an IndexState enum.");
    }

    public override void Write(Utf8JsonWriter writer, IndexState value, JsonSerializerOptions options)
    {
        EnumMemberAttribute? enumMemberAttr =
            value.GetType().GetMember(value.ToString())[0].GetCustomAttribute(typeof(EnumMemberAttribute)) as EnumMemberAttribute;

        if (enumMemberAttr != null)
        {
            writer.WriteStringValue(enumMemberAttr.Value);
        }
        else
        {
            throw new JsonException($"Unable to find EnumMember attribute for IndexState '{value}'.");
        }
    }
}
