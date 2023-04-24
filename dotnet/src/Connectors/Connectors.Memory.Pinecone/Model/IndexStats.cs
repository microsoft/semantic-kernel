using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// DescribeIndexStatsResponse
/// </summary>
public class IndexStats
{

    /// <summary>
    /// Initializes a new instance of the <see cref="IndexStats" /> class.
    /// </summary>
    /// <param name="namespaces">namespaces.</param>
    /// <param name="dimension">The number of dimensions in the vector representation.</param>
    /// <param name="indexFullness">The fullness of the index, regardless of whether a metadata filter expression was passed. The granularity of this metric is 10%..</param>
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
    /// <value>The number of dimensions in the vector representation</value>
    [JsonPropertyName("dimension")]
    public int Dimension { get; set; }

    /// <summary>
    /// The fullness of the index, regardless of whether a metadata filter expression was passed. The granularity of this metric is 10%.
    /// </summary>
    /// <value>The fullness of the index, regardless of whether a metadata filter expression was passed. The granularity of this metric is 10%.</value>
    [JsonPropertyName("indexFullness")]
    public float IndexFullness { get; set; }

    /// <summary>
    /// Gets or Sets TotalVectorCount
    /// </summary>
    [JsonPropertyName("totalVectorCount")]
    public long TotalVectorCount { get; set; }

    /// <summary>
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        StringBuilder sb = new();
        sb.Append("DescribeIndexStatsResponse {\n");
        sb.Append("  Namespaces: ").Append('\n');

        foreach (KeyValuePair<string, IndexNamespaceStats> item in this.Namespaces)
        {
            sb.Append("    ").Append(item.Key).Append(": ").Append(item.Value.VectorCount).Append('\n');
        }
        sb.Append("  Dimension: ").Append(this.Dimension).Append('\n');
        sb.Append("  IndexFullness: ").Append(this.IndexFullness).Append('\n');
        sb.Append("  TotalVectorCount: ").Append(this.TotalVectorCount).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

}
