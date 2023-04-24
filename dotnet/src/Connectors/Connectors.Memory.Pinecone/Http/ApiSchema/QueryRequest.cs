using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// QueryRequest
/// </summary>
internal class QueryRequest
{

    /// <summary>
    /// An index namespace name
    /// </summary>
    /// <value>An index namespace name</value>
    /// <example>&quot;namespace-0&quot;</example>
    [JsonPropertyName("namespace")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Namespace { get; set; }

    /// <summary>
    /// The number of results to return for each query.
    /// </summary>
    /// <value>The number of results to return for each query.</value>
    [JsonPropertyName("topK")]
    [JsonRequired]
    public long TopK { get; set; }

    /// <summary>
    /// If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.
    /// </summary>
    /// <value>If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.</value>
    [JsonPropertyName("filter")]
    public Dictionary<string, object>? Filter { get; set; }

    /// <summary>
    /// Vector dense data. This should be the same length as the dimension of the index being queried.
    /// </summary>
    /// <value>Vector dense data. This should be the same length as the dimension of the index being queried.</value>
    [JsonPropertyName("vector")]
    public IEnumerable<float> Vector { get; set; }

    /// <summary>
    /// The unique ID of a vector
    /// </summary>
    /// <value>The unique ID of a vector</value>
    /// <example>&quot;vector-0&quot;</example>
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

    public static QueryRequest QueryIndex(IEnumerable<float> vector)
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
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        StringBuilder sb = new();
        sb.Append("QueryRequest {\n");
        sb.Append("  Vector: ").Append(this.Vector).Append('\n');
        sb.Append("  TopK: ").Append(this.TopK).Append('\n');
        sb.Append("  Namespace: ").Append(this.Namespace).Append('\n');
        sb.Append("  IncludeValues: ").Append(this.IncludeValues).Append('\n');
        sb.Append("  IncludeMetadata: ").Append(this.IncludeMetadata).Append('\n');
        sb.Append("  SparseVector: ").Append(this.SparseVector).Append('\n');
        sb.Append("  Id: ").Append(this.Id).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QueryRequest" /> class.
    /// </summary>
    [JsonConstructor]
    private QueryRequest(IEnumerable<float> values)
    {
        this.Vector = values;
    }

}
