// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Query parameters for use in a query request.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public sealed class Query
{
    /// <summary>
    /// The number of results to return for each query.
    /// </summary>
    public int TopK { get; set; }

    /// <summary>
    /// The namespace of the index to query. If not specified, the default namespace is used.
    /// </summary>
    public string? Namespace { get; set; }

    /// <summary>
    /// If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.
    /// </summary>
    public Dictionary<string, object>? Filter { get; set; }

    /// <summary>
    /// Vector dense data. This should be the same length as the dimension of the index being queried.
    /// </summary>
    public ReadOnlyMemory<float> Vector { get; set; }

    /// <summary>
    /// The unique ID of a vector
    /// </summary>
    public string? Id { get; set; }

    /// <summary>
    /// Gets or Sets SparseVector
    /// </summary>
    public SparseVectorData? SparseVector { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="Query" /> class.
    /// </summary>
    /// <param name="topK">The number of results to return for each query.</param>
    public static Query Create(int topK)
    {
        return new Query()
        {
            TopK = topK
        };
    }

    /// <summary>
    /// Sets vector for <see cref="Query"/> instance.
    /// </summary>
    /// <param name="vector">Vector dense data. This should be the same length as the dimension of the index being queried.</param>
    public Query WithVector(ReadOnlyMemory<float> vector)
    {
        this.Vector = vector;
        return this;
    }

    /// <summary>
    /// Sets index namespace for <see cref="Query"/> instance.
    /// </summary>
    /// <param name="indexNamespace">The namespace of the index to query. If not specified, the default namespace is used.</param>
    public Query InNamespace(string? indexNamespace)
    {
        this.Namespace = indexNamespace;
        return this;
    }

    /// <summary>
    /// Sets filter for <see cref="Query"/> instance.
    /// </summary>
    /// <param name="filter">If this parameter is present, the operation only affects vectors that satisfy the filter.</param>
    public Query WithFilter(Dictionary<string, object>? filter)
    {
        this.Filter = filter;
        return this;
    }

    /// <summary>
    /// Sets sparse vector data for <see cref="Query"/> instance.
    /// </summary>
    /// <param name="sparseVector">Vector sparse data. Represented as a list of indices and a list of corresponded values, which must be the same length.</param>
    public Query WithSparseVector(SparseVectorData? sparseVector)
    {
        this.SparseVector = sparseVector;
        return this;
    }

    /// <summary>
    /// Sets unique vector id for <see cref="Query"/> instance.
    /// </summary>
    /// <param name="id">The unique ID of a vector.</param>
    public Query WithId(string id)
    {
        this.Id = id;
        return this;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Query" /> class.
    /// </summary>
    [JsonConstructor]
    private Query()
    {
    }
}
