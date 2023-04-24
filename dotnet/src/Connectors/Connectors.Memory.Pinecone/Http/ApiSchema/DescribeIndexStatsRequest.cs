using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// DescribeIndexStatsRequest
/// </summary>
internal class DescribeIndexStatsRequest
{
    /// <summary>
    /// If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.
    /// </summary>
    /// <value>If this parameter is present, the operation only affects vectors that satisfy the filter. See https://www.pinecone.io/docs/metadata-filtering/.</value>
    [JsonPropertyName("filter")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Dictionary<string, object>? Filter { get; set; }

    public static DescribeIndexStatsRequest GetIndexStats()
    {
        return new DescribeIndexStatsRequest();
    }

    public DescribeIndexStatsRequest WithFilter(Dictionary<string, object>? filter)
    {
        this.Filter = filter;
        return this;
    }

    public HttpRequestMessage Build()
    {
        return this.Filter == null
            ? HttpRequest.CreatePostRequest("/describe_index_stats")
            : HttpRequest
                .CreatePostRequest("/describe_index_stats", this);
    }

    /// <summary>
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        StringBuilder sb = new();
        sb.Append("class DescribeIndexStatsRequest {\n");
        sb.Append("  Filter: ").Append(this.Filter).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

    #region private ================================================================================

    private DescribeIndexStatsRequest()
    {
    }

    #endregion

}
