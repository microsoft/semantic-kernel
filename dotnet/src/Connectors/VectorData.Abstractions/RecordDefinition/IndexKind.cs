// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a list of well-known index types that can be used to index vectors.
/// </summary>
/// <remarks>
/// Not all Vector Store connectors support all index types, and some connectors might
/// support additional index types that aren't defined here. See the documentation
/// for each connector for more information on what is supported.
/// </remarks>
public static class IndexKind
{
    /// <summary>
    /// Hierarchical Navigable Small World, which performs an approximate nearest neighbour (ANN) search.
    /// </summary>
    /// <remarks>
    /// This search has lower accuracy than exhaustive k nearest neighbor, but is faster and more efficient.
    /// </remarks>
    public const string Hnsw = nameof(Hnsw);

    /// <summary>
    /// Brute force search to find the nearest neighbors.
    /// </summary>
    /// <remarks>
    /// This search calculates the distances between all pairs of data points, so it has a linear time complexity that grows directly proportional to the number of points.
    /// It's also referred to as exhaustive k nearest neighbor in some databases.
    /// This search has high recall accuracy, but is slower and more expensive than HNSW.
    /// It works better with smaller datasets.
    /// </remarks>
    public const string Flat = nameof(Flat);

    /// <summary>
    /// Inverted File with Flat Compression.
    /// </summary>
    /// <remarks>
    /// This search is designed to enhance search efficiency by narrowing the search area through the use of neighbor partitions or clusters.
    /// Also referred to as approximate nearest neighbor (ANN) search.
    /// </remarks>
    public const string IvfFlat = nameof(IvfFlat);

    /// <summary>
    /// Disk-based Approximate Nearest Neighbor algorithm designed for efficiently searching for approximate nearest neighbors (ANN) in high-dimensional spaces.
    /// </summary>
    /// <remarks>
    /// The primary focus of DiskANN is to handle large-scale datasets that can't fit entirely into memory, leveraging disk storage to store the data while maintaining fast search times.
    /// </remarks>
    public const string DiskAnn = nameof(DiskAnn);

    /// <summary>
    /// Index that compresses vectors using DiskANN-based quantization methods for better efficiency in the kNN search.
    /// </summary>
    public const string QuantizedFlat = nameof(QuantizedFlat);

    /// <summary>
    /// Dynamic index allows to automatically switch from <see cref="Flat"/> to <see cref="Hnsw"/> indexes.
    /// </summary>
    public const string Dynamic = nameof(Dynamic);
}
