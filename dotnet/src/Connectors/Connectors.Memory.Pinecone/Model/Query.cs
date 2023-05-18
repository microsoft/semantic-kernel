// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
///  Query parameters for use in a query request.
/// </summary>
public sealed class Query
{
    /// <summary>
    /// The number of results to return for each query.
    /// </summary>
    public int TopK { get; set; }

    /// <summary>
    ///  The namespace of the index to query. If not specified, the default namespace is used.
    /// </summary>
    public string? Namespace { get; set; }

    /// <summary>
    /// If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.
    /// </summary>
    public Dictionary<string, object>? Filter { get; set; }

    /// <summary>
    /// Vector dense data. This should be the same length as the dimension of the index being queried.
    /// </summary>
    public IEnumerable<float>? Vector { get; set; }

    /// <summary>
    /// The unique ID of a vector
    /// </summary>
    public string? Id { get; set; }

    /// <summary>
    /// Gets or Sets SparseVector
    /// </summary>
    public SparseVectorData? SparseVector { get; set; }

    public static Query Create(int topK)
    {
        return new Query()
        {
            TopK = topK
        };
    }

    public Query WithVector(IEnumerable<float>? vector)
    {
        this.Vector = vector;
        return this;
    }

    public Query InNamespace(string? indexNamespace)
    {
        this.Namespace = indexNamespace;
        return this;
    }

    public Query WithFilter(Dictionary<string, object>? filter)
    {
        this.Filter = filter;
        return this;
    }

    public Query WithSparseVector(SparseVectorData? sparseVector)
    {
        this.SparseVector = sparseVector;
        return this;
    }

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
