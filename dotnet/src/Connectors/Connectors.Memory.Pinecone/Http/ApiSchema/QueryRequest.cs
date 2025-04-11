// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// QueryRequest
/// See https://docs.pinecone.io/reference/query
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class QueryRequest
{
    /// <summary>
    /// An index namespace name
    /// </summary>
    [JsonPropertyName("namespace")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Namespace { get; set; }

    /// <summary>
    /// The number of results to return for each query.
    /// </summary>
    [JsonPropertyName("topK")]
    public long TopK { get; set; }

    /// <summary>
    /// If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.
    /// </summary>
    [JsonPropertyName("filter")]
    public Dictionary<string, object>? Filter { get; set; }

    /// <summary>
    /// Vector dense data. This should be the same length as the dimension of the index being queried.
    /// </summary>
    [JsonPropertyName("vector")]
    public ReadOnlyMemory<float> Vector { get; set; }

    /// <summary>
    /// The unique ID of a vector
    /// </summary>
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    /// <summary>
    /// Sparse vector data. If this is present, the query will be performed using a sparse vector in addition to the dense vector.
    /// </summary>
    [JsonPropertyName("sparseVector")]
    public SparseVectorData? SparseVector { get; set; }

    /// <summary>
    /// Whether to include the vector values in the response. If false, only the vector IDs are returned.
    /// </summary>
    [JsonPropertyName("includeValues")]
    public bool IncludeValues { get; set; }

    /// <summary>
    /// Whether to include the vector metadata in the response. If false, only the vector IDs are returned.
    /// </summary>
    [JsonPropertyName("includeMetadata")]
    public bool IncludeMetadata { get; set; }

    public static QueryRequest QueryIndex(Query query)
    {
        return new QueryRequest(query.Vector)
        {
            TopK = query.TopK,
            Filter = query.Filter,
            Namespace = query.Namespace,
            SparseVector = query.SparseVector,
            Id = query.Id
        };
    }

    public QueryRequest WithMetadata(bool includeMetadata)
    {
        this.IncludeMetadata = includeMetadata;
        return this;
    }

    public QueryRequest WithEmbeddings(bool includeValues)
    {
        this.IncludeValues = includeValues;
        return this;
    }

    public HttpRequestMessage Build()
    {
        if (this.Filter is not null)
        {
            this.Filter = PineconeUtils.ConvertFilterToPineconeFilter(this.Filter);
        }

        HttpRequestMessage? request = HttpRequest.CreatePostRequest(
            "/query",
            this);

        request.Headers.Add("accept", "application/json");

        return request;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QueryRequest" /> class.
    /// </summary>
    [JsonConstructor]
    private QueryRequest(ReadOnlyMemory<float> values)
    {
        this.Vector = values;
    }
}
