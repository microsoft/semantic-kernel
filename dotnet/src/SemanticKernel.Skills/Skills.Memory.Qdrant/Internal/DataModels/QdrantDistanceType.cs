// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

[JsonConverter(typeof(JsonStringEnumConverter))]
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

public static class QdrantDistanceUtils
{
    public static string DistanceTypeToString(QdrantDistanceType x)
    {
        return x switch
        {
            QdrantDistanceType.Cosine => "Cosine",
            QdrantDistanceType.DotProduct => "DotProduct",
            QdrantDistanceType.Euclidean => "Euclidean",
            QdrantDistanceType.Manhattan => "Manhattan",
            _ => throw new NotSupportedException($"Distance type {Enum.GetName(typeof(QdrantDistanceType), x)} not supported")
        };
    }

    public static QdrantDistanceType DistanceStringToType(string distanceType)
    {
        return distanceType switch
        {
            "Cosine" => QdrantDistanceType.Cosine,
            "DotProduct" => QdrantDistanceType.DotProduct,
            "Euclidean" => QdrantDistanceType.Euclidean,
            "Manhattan" => QdrantDistanceType.Manhattan,
            _ => throw new NotSupportedException($"Distance type {distanceType} not supported")
        };
    }
}
