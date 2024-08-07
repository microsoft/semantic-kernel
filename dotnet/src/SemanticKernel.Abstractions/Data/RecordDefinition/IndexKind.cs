// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Defines a list of well known index types that can be used to index vectors.
/// </summary>
/// <remarks>
/// Not all Vector Store connectors support all index types and some connectors may
/// support additional index types that are not defined here. See the documentation
/// for each connector for more information on what is supported.
/// </remarks>
[Experimental("SKEXP0001")]
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
}
