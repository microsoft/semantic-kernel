using System.Net.Http;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// IndexConfiguration
/// </summary>
internal class ConfigureIndexRequest
{
    public string IndexName { get; set; }

    /// <summary>
    /// Gets or Sets PodType
    /// </summary>
    [JsonPropertyName("pod_type")]
    public PodType PodType { get; set; }

    /// <summary>
    /// The desired number of replicas for the index.
    /// </summary>
    /// <value>The desired number of replicas for the index.</value>
    [JsonPropertyName("replicas")]
    public int Replicas { get; set; }

    public static ConfigureIndexRequest Create(string indexName)
    {
        return new ConfigureIndexRequest(indexName);
    }

    public ConfigureIndexRequest WithPodType(PodType podType)
    {
        this.PodType = podType;
        return this;
    }

    public ConfigureIndexRequest NumberOfReplicas(int replicas)
    {
        this.Replicas = replicas;
        return this;
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePatchRequest($"/database/{this.IndexName}", this);
    }

    /// <summary>
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        StringBuilder sb = new();
        sb.Append("IndexConfiguration {\n");
        sb.Append("  Replicas: ").Append(this.Replicas).Append('\n');
        sb.Append("  PodType: ").Append(this.PodType).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

    #region private ================================================================================

    /// <summary>
    /// Initializes a new instance of the <see cref="ConfigureIndexRequest" /> class.
    /// </summary>
    /// <param name="indexName"> Name of the index.</param>
    private ConfigureIndexRequest(string indexName)
    {
        this.IndexName = indexName;
    }

    #endregion

}
