// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// QueryRequest
/// See https://docs.pinecone.io/reference/query
/// </summary>
internal class QueryRequest
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
    public IEnumerable<float>? Vector { get; set; }

    /// <summary>
    /// The unique ID of a vector
    /// </summary>
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    /// <summary>
    /// Gets or Sets SparseVector
    /// </summary>
    [JsonPropertyName("sparseVector")]
    public SparseVectorData? SparseVector { get; set; }

    /// <summary>
    /// Gets or Sets IncludeValues
    /// </summary>
    [JsonPropertyName("includeValues")]
    public bool IncludeValues { get; set; }

    /// <summary>
    /// Gets or Sets IncludeMetadata
    /// </summary>
    [JsonPropertyName("includeMetadata")]
    public bool IncludeMetadata { get; set; }

    public static QueryRequest QueryIndex(IEnumerable<float>? vector = null)
    {
        return new QueryRequest(vector);
    }

    public QueryRequest WithTopK(long topK)
    {
        this.TopK = topK;
        return this;
    }

    public QueryRequest WithFilter(Dictionary<string, object>? filter)
    {
        this.Filter = filter;
        return this;
    }

    public QueryRequest WithMetadata(bool includeMetadata)
    {
        this.IncludeMetadata = includeMetadata;
        return this;
    }

    public QueryRequest WithVectors(bool includeValues)
    {
        this.IncludeValues = includeValues;
        return this;
    }

    public QueryRequest InNamespace(string? nameSpace)
    {
        this.Namespace = nameSpace;
        return this;
    }

    public QueryRequest WithSparseVector(SparseVectorData? sparseVector)
    {
        this.SparseVector = sparseVector;
        return this;
    }

    public QueryRequest WithId(string? id)
    {
        this.Id = id;
        return this;
    }

    public HttpRequestMessage Build()
    {
        if (this.Filter != null)
        {
            this.Filter = PineconeUtils.ConvertFilterToPineconeFilter(this.Filter);
        }

        HttpRequestMessage? request = HttpRequest.CreatePostRequest(
            "/query",
            this);

        return request;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QueryRequest" /> class.
    /// </summary>
    [JsonConstructor]
    private QueryRequest(IEnumerable<float>? values = null)
    {
        this.Vector = values;
    }

}
