// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Reflection;
using System.Runtime.Serialization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// The vector similarity metric of the index
/// </summary>
/// <value>The vector similarity metric of the index</value>
[JsonConverter(typeof(IndexMetricJsonConverter))]
public enum IndexMetric
{
    /// <summary>
    /// Enum Euclidean for value: euclidean
    /// </summary>
    [EnumMember(Value = "euclidean")]
    Euclidean = 1,

    /// <summary>
    /// Enum Cosine for value: cosine
    /// </summary>
    [EnumMember(Value = "cosine")]
    Cosine = 2,

    /// <summary>
    /// Enum Dotproduct for value: dotproduct
    /// </summary>
    [EnumMember(Value = "dotproduct")]
    Dotproduct = 3

}

public class IndexMetricJsonConverter : JsonConverter<IndexMetric>
{
    public override IndexMetric Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? stringValue = reader.GetString();

        foreach (object? enumValue in from object? enumValue in Enum.GetValues(typeToConvert)
                                      let enumMemberAttr =
                                          typeToConvert.GetMember(enumValue.ToString())[0].GetCustomAttribute(typeof(EnumMemberAttribute)) as EnumMemberAttribute
                                      where enumMemberAttr != null && enumMemberAttr.Value == stringValue
                                      select enumValue)
        {
            return (IndexMetric)enumValue;
        }
        throw new JsonException($"Unable to parse '{stringValue}' as an IndexMetric enum.");
    }

    public override void Write(Utf8JsonWriter writer, IndexMetric value, JsonSerializerOptions options)
    {

        if (value.GetType().GetMember(value.ToString())[0].GetCustomAttribute(typeof(EnumMemberAttribute)) is EnumMemberAttribute enumMemberAttr)
        {
            writer.WriteStringValue(enumMemberAttr.Value);
        }
        else
        {
            throw new JsonException($"Unable to find EnumMember attribute for IndexMetric '{value}'.");
        }
    }
}
