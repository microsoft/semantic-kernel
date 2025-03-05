// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a list of well known distance functions that can be used to compare vectors.
/// </summary>
/// <remarks>
/// Not all Vector Store connectors support all distance functions and some connectors may
/// support additional distance functions that are not defined here. See the documentation
/// for each connector for more information on what is supported.
/// </remarks>
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
    /// The higher the value, the more similar the vectors.
    /// </remarks>
    public const string DotProductSimilarity = nameof(DotProductSimilarity);

    /// <summary>
    /// Measures both the length and angle between two vectors.
    /// </summary>
    /// <remarks>
    /// The value of NegativeDotProduct = -1 * DotProductSimilarity.
    /// The higher the value, the greater the distance between the vectors and the less similar the vectors.
    /// </remarks>
    public const string NegativeDotProductSimilarity = nameof(NegativeDotProductSimilarity);

    /// <summary>
    /// Measures the Euclidean distance between two vectors.
    /// </summary>
    /// <remarks>
    /// Also known as l2-norm.
    /// </remarks>
    public const string EuclideanDistance = nameof(EuclideanDistance);

    /// <summary>
    /// Measures the Euclidean squared distance between two vectors.
    /// </summary>
    /// <remarks>
    /// Also known as l2-squared.
    /// </remarks>
    public const string EuclideanSquaredDistance = nameof(EuclideanSquaredDistance);

    /// <summary>
    /// Number of differences between vectors at each dimensions.
    /// </summary>
    public const string Hamming = nameof(Hamming);

    /// <summary>
    /// Measures the Manhattan distance between two vectors.
    /// </summary>
    public const string ManhattanDistance = nameof(ManhattanDistance);
}
