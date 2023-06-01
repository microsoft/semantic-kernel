// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant;

/// <summary>
/// The vector distance type used by Qdrant.
/// </summary>
[JsonConverter(typeof(QdrantDistanceTypeJsonConverter))]
public enum QdrantDistanceType
{
    /// <summary>
    /// Cosine of the angle between vectors, aka dot product scaled by magnitude. Cares only about angle difference.
    /// </summary>
    Cosine,

    /// <summary>
    /// Consider angle and distance (magnitude) of vectors.
    /// </summary>
    DotProduct,

    /// <summary>
    /// Pythagorean(theorem) distance of 2 multidimensional points.
    /// </summary>
    Euclidean,

    /// <summary>
    /// Sum of absolute differences between points across all the dimensions.
    /// </summary>
    Manhattan,

    /// <summary>
    /// Assuming only the most significant dimension is relevant.
    /// </summary>
    Chebyshev,

    /// <summary>
    /// Generalization of Euclidean and Manhattan.
    /// </summary>
    Minkowski,
}

// TODO https://github.com/dotnet/runtime/issues/79311
internal sealed class QdrantDistanceTypeJsonConverter : JsonConverter<QdrantDistanceType>
{
    public override QdrantDistanceType Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? stringValue = reader.GetString();
        return
            nameof(QdrantDistanceType.Cosine).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? QdrantDistanceType.Cosine :
            nameof(QdrantDistanceType.DotProduct).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? QdrantDistanceType.DotProduct :
            nameof(QdrantDistanceType.Euclidean).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? QdrantDistanceType.Euclidean :
            nameof(QdrantDistanceType.Manhattan).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? QdrantDistanceType.Manhattan :
            nameof(QdrantDistanceType.Chebyshev).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? QdrantDistanceType.Chebyshev :
            nameof(QdrantDistanceType.Minkowski).Equals(stringValue, StringComparison.OrdinalIgnoreCase) ? QdrantDistanceType.Minkowski :
            throw new JsonException($"Unable to parse '{stringValue}'");
    }

    public override void Write(Utf8JsonWriter writer, QdrantDistanceType value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value switch
        {
            QdrantDistanceType.Cosine => nameof(QdrantDistanceType.Cosine),
            QdrantDistanceType.DotProduct => nameof(QdrantDistanceType.DotProduct),
            QdrantDistanceType.Euclidean => nameof(QdrantDistanceType.Euclidean),
            QdrantDistanceType.Manhattan => nameof(QdrantDistanceType.Manhattan),
            QdrantDistanceType.Chebyshev => nameof(QdrantDistanceType.Chebyshev),
            QdrantDistanceType.Minkowski => nameof(QdrantDistanceType.Minkowski),
            _ => throw new JsonException($"Unable to find value '{value}'."),
        });
    }
}
