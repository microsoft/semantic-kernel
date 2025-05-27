// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a list of well-known distance functions that can be used to compare vectors.
/// </summary>
/// <remarks>
/// Not all Vector Store connectors support all distance functions, and some connectors might
/// support additional distance functions that aren't defined here.
/// For more information on what's supported, see the documentation for each connector.
/// </remarks>
public static class DistanceFunction
{
    /// <summary>
    /// Specifies the function that measures the cosine (angular) similarity between two vectors.
    /// </summary>
    /// <remarks>
    /// Cosine similarity measures only the angle between the two vectors, without taking into account the length of the vectors.
    /// ConsineSimilarity = 1 - CosineDistance.
    /// -1 means vectors are opposite.
    /// 0 means vectors are orthogonal.
    /// 1 means vectors are identical.
    /// </remarks>
    public const string CosineSimilarity = nameof(CosineSimilarity);

    /// <summary>
    /// Specifies the function that measures the cosine (angular) distance between two vectors.
    /// </summary>
    /// <remarks>
    /// CosineDistance = 1 - CosineSimilarity.
    /// 2 means vectors are opposite.
    /// 1 means vectors are orthogonal.
    /// 0 means vectors are identical.
    /// </remarks>
    public const string CosineDistance = nameof(CosineDistance);

    /// <summary>
    /// Specifies the dot product similarity function, which measures both the length and angle between two vectors.
    /// </summary>
    /// <remarks>
    /// The higher the value, the more similar the vectors.
    /// </remarks>
    public const string DotProductSimilarity = nameof(DotProductSimilarity);

    /// <summary>
    /// Specifies the negative dot product similarity function, which measures both the length and angle between two vectors.
    /// </summary>
    /// <remarks>
    /// The value of NegativeDotProduct = -1 * DotProductSimilarity.
    /// The higher the value, the greater the distance between the vectors and the less similar the vectors.
    /// </remarks>
    public const string NegativeDotProductSimilarity = nameof(NegativeDotProductSimilarity);

    /// <summary>
    /// Specifies the function that measures the Euclidean distance between two vectors.
    /// </summary>
    /// <remarks>
    /// Also known as l2-norm.
    /// </remarks>
    public const string EuclideanDistance = nameof(EuclideanDistance);

    /// <summary>
    /// Specifies the function that measures the Euclidean squared distance between two vectors.
    /// </summary>
    /// <remarks>
    /// Also known as l2-squared.
    /// </remarks>
    public const string EuclideanSquaredDistance = nameof(EuclideanSquaredDistance);

    /// <summary>
    /// Specifies the function that measures the number of differences between vectors at each dimension.
    /// </summary>
    public const string HammingDistance = nameof(HammingDistance);

    /// <summary>
    /// Specifies the function that measures the Manhattan distance between two vectors.
    /// </summary>
    public const string ManhattanDistance = nameof(ManhattanDistance);
}
