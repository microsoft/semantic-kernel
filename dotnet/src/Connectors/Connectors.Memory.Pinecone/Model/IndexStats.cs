// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Index parameters.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public class IndexStats
{
    /// <summary>
    /// Initializes a new instance of the <see cref="IndexStats" /> class.
    /// </summary>
    /// <param name="namespaces">Namespaces.</param>
    /// <param name="dimension">The number of dimensions in the vector representation.</param>
    /// <param name="indexFullness">The fullness of the index, regardless of whether a metadata filter expression was passed. The granularity of this metric is 10%.</param>
    /// <param name="totalVectorCount">totalVectorCount.</param>
    public IndexStats(
        Dictionary<string, IndexNamespaceStats> namespaces,
        int dimension = default,
        float indexFullness = default,
        long totalVectorCount = default)
    {
        this.Namespaces = namespaces;
        this.Dimension = dimension;
        this.IndexFullness = indexFullness;
        this.TotalVectorCount = totalVectorCount;
    }

    /// <summary>
    /// Gets or Sets Namespaces
    /// </summary>
    [JsonPropertyName("namespaces")]
    public Dictionary<string, IndexNamespaceStats> Namespaces { get; set; }

    /// <summary>
    /// The number of dimensions in the vector representation
    /// </summary>
    [JsonPropertyName("dimension")]
    public int Dimension { get; set; }

    /// <summary>
    /// The fullness of the index, regardless of whether a metadata filter expression was passed. The granularity of this metric is 10%.
    /// </summary>
    [JsonPropertyName("indexFullness")]
    public float IndexFullness { get; set; }

    /// <summary>
    /// Gets or Sets TotalVectorCount
    /// </summary>
    [JsonPropertyName("totalVectorCount")]
    public long TotalVectorCount { get; set; }
}
