// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a list of well known index types that can be used to index vectors.
/// </summary>
/// <remarks>
/// Not all Vector Store connectors support all index types and some connectors may
/// support additional index types that are not defined here. See the documentation
/// for each connector for more information on what is supported.
/// </remarks>
public static class IndexKind
{
    /// <summary>
    /// Hierarchical Navigable Small World, which performs an approximate nearest neighbour (ANN) search.
    /// </summary>
    /// <remarks>
    /// Lower accuracy than exhaustive k nearest neighbor, but faster and more efficient.
    /// </remarks>
    public const string Hnsw = nameof(Hnsw);

    /// <summary>
    /// Does a brute force search to find the nearest neighbors.
    /// Calculates the distances between all pairs of data points, so has a linear time complexity, that grows directly proportional to the number of points.
    /// Also referred to as exhaustive k nearest neighbor in some databases.
    /// </summary>
    /// <remarks>
    /// High recall accuracy, but slower and more expensive than HNSW.
    /// Better with smaller datasets.
    /// </remarks>
    public const string Flat = nameof(Flat);

    /// <summary>
    /// Inverted File with Flat Compression. Designed to enhance search efficiency by narrowing the search area through the use of neighbor partitions or clusters.
    /// Also referred to as approximate nearest neighbor (ANN) search.
    /// </summary>
    public const string IvfFlat = nameof(IvfFlat);

    /// <summary>
    /// Disk-based Approximate Nearest Neighbor algorithm designed for efficiently searching for approximate nearest neighbors (ANN) in high-dimensional spaces.
    /// The primary focus of DiskANN is to handle large-scale datasets that cannot fit entirely into memory, leveraging disk storage to store the data while maintaining fast search times.
    /// </summary>
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
