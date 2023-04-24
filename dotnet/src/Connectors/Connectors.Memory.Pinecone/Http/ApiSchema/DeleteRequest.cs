using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// DeleteRequest
/// </summary>
internal class DeleteRequest
{

    /// <summary>
    /// Gets or Sets Ids
    /// </summary>
    [JsonPropertyName("ids")]
    public IEnumerable<string> Ids { get; set; }

    /// <summary>
    /// Gets or Sets DeleteAll
    /// </summary>
    [JsonPropertyName("deleteAll")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? DeleteAll { get; set; }

    /// <summary>
    /// An index namespace name
    /// </summary>
    /// <value>An index namespace name</value>
    /// <example>&quot;namespace-0&quot;</example>
    [JsonPropertyName("namespace")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Namespace { get; set; }

    /// <summary>
    /// If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.
    /// </summary>
    /// <value>If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.</value>
    [JsonPropertyName("filter")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Dictionary<string, object>? Filter { get; set; }

    public static DeleteRequest DeleteAllVectors()
    {
        return new DeleteRequest(true);
    }

    public static DeleteRequest ClearNamespace(string nameSpace)
    {
        return new DeleteRequest(true)
        {
            Namespace = nameSpace
        };
    }

    public static DeleteRequest DeleteVectors(IEnumerable<string> ids)
    {
        return new DeleteRequest(ids);
    }

    public DeleteRequest FilterBy(Dictionary<string, object>? filter)
    {
        this.Filter = filter;
        return this;
    }

    public DeleteRequest FromNamespace(string? nameSpace)
    {
        this.Namespace = nameSpace;
        return this;
    }

    public DeleteRequest Clear(bool deleteAll)
    {
        this.DeleteAll = deleteAll;
        return this;
    }

    public HttpRequestMessage Build()
    {
        if (this.Filter != null)
        {
            this.Filter = PineconeUtils.ConvertFilterToPineconeFilter(this.Filter);
        }

        HttpRequestMessage? request = HttpRequest.CreatePostRequest(
            "/vectors/delete",
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
        sb.Append("DeleteRequest {\n");
        sb.Append("  Ids: ").Append(this.Ids).Append('\n');
        sb.Append("  DeleteAll: ").Append(this.Clear).Append('\n');
        sb.Append("  Namespace: ").Append(this.Namespace).Append('\n');
        sb.Append("  Filter: ").Append(this.Filter).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

    #region private ================================================================================

    private DeleteRequest(IEnumerable<string> ids)
    {
        this.Ids = ids;
    }

    private DeleteRequest(bool clear)
    {
        this.Ids = new List<string>();
        this.DeleteAll = clear;
    }

    #endregion

}
