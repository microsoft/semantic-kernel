// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Defines a list of well known distance functions that can be used to compare vectors.
/// </summary>
/// <remarks>
/// Not all Vector Store connectors support all distance functions and some connectors may
/// support additional distance functions that are not defined here. See the documentation
/// for each connector for more information on what is supported.
/// </remarks>
[Experimental("SKEXP0001")]
public static class DistanceFunction
{
    /// <summary>
    /// The cosine (angular) similarity between two vectors.
    /// </summary>
    /// <remarks>
    /// Measures only the angle between the two vectors, without taking into account the length of the vectors.
    /// ConsineSimilarity = 1 - CosineDistance.
    /// -1 means vectors are opposite.
    /// 0 means vectors are orthogonal.
    /// 1 means vectors are identical.
    /// </remarks>
    public const string CosineSimilarity = nameof(CosineSimilarity);

    /// <summary>
    /// The cosine (angular) similarity between two vectors.
    /// </summary>
    /// <remarks>
    /// CosineDistance = 1 - CosineSimilarity.
    /// 2 means vectors are opposite.
    /// 1 means vectors are orthogonal.
    /// 0 means vectors are identical.
    /// </remarks>
    public const string CosineDistance = nameof(CosineDistance);

    /// <summary>
    /// Measures both the length and angle between two vectors.
    /// </summary>
    /// <remarks>
    /// Same as cosine similarity if the vectors are the same length, but more performant.
    /// </remarks>
    public const string DotProductSimilarity = nameof(DotProductSimilarity);

    /// <summary>
    /// Measures the Euclidean distance between two vectors.
    /// </summary>
    /// <remarks>
    /// Also known as l2-norm.
    /// </remarks>
    public const string EuclideanDistance = nameof(EuclideanDistance);

    /// <summary>
    /// Measures the Manhattan distance between two vectors.
    /// </summary>
    public const string ManhattanDistance = nameof(ManhattanDistance);
}
