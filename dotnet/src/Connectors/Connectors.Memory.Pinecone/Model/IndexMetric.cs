// Copyright (c) Microsoft. All rights reserved.

using System;
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
    /// Default value.
    /// </summary>
    None = 0,

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

// TODO https://github.com/dotnet/runtime/issues/79311
internal sealed class IndexMetricJsonConverter : JsonConverter<IndexMetric>
{
    public override IndexMetric Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? stringValue = reader.GetString();
        return
            nameof(IndexMetric.Euclidean).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? IndexMetric.Euclidean :
            nameof(IndexMetric.Cosine).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? IndexMetric.Cosine :
            nameof(IndexMetric.Dotproduct).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? IndexMetric.Dotproduct :
            throw new JsonException($"Unable to parse '{stringValue}'");
    }

    public override void Write(Utf8JsonWriter writer, IndexMetric value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value switch
        {
            IndexMetric.Euclidean => "euclidean",
            IndexMetric.Cosine => "cosine",
            IndexMetric.Dotproduct => "dotproduct",
            _ => throw new JsonException($"Unable to find value '{value}'."),
        });
    }
}
