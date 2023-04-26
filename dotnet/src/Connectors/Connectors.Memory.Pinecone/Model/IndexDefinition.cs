using System.Net.Http;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// IndexDefinition
/// </summary>
public class IndexDefinition
{

    /// <summary>
    /// The unique name of an index.
    /// </summary>
    /// <value>The unique name of an index.</value>
    [JsonPropertyName("name")]
    public string Name { get; set; }

    /// <summary>
    /// Gets or Sets Metric
    /// </summary>
    [JsonPropertyName("metric")]
    public IndexMetric Metric { get; set; } = IndexMetric.Cosine;

    /// <summary>
    /// Gets or Sets PodType
    /// </summary>
    [JsonPropertyName("pod_type")]
    public PodType PodType { get; set; } = PodType.P1X1;

    /// <summary>
    /// The number of dimensions in the vector representation
    /// </summary>
    /// <value>The number of dimensions in the vector representation</value>
    [JsonPropertyName("dimension")]
    public int Dimension { get; set; }

    /// <summary>
    /// The number of pods for the index to use,including replicas.
    /// </summary>
    /// <value>The number of pods for the index to use,including replicas.</value>
    [JsonPropertyName("pods")]
    public int Pods { get; set; }

    /// <summary>
    /// The number of replicas. Replicas duplicate your index. They provide higher availability and throughput.
    /// </summary>
    /// <value>The number of replicas. Replicas duplicate your index. They provide higher availability and throughput.</value>
    [JsonPropertyName("replicas")]
    public int Replicas { get; set; }

    /// <summary>
    /// Gets or Sets Shards
    /// </summary>
    [JsonPropertyName("shards")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public int? Shards { get; set; }

    /// <summary>
    /// Gets or Sets MetadataConfig
    /// </summary>
    [JsonPropertyName("metadata_config")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public MetadataIndexConfig? MetadataConfig { get; set; }

    /// <summary>
    /// The unique name of a collection.
    /// </summary>
    /// <value>The unique name of a collection.</value>
    /// <example>&quot;example&quot;</example>
    [JsonPropertyName("source_collection")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? SourceCollection { get; set; }

    public static IndexDefinition Create(string name)
    {
        return new IndexDefinition(name);
    }

    public IndexDefinition WithDimension(int dimension)
    {
        this.Dimension = dimension;
        return this;
    }

    public IndexDefinition WithMetric(IndexMetric metric)
    {
        this.Metric = metric;
        return this;
    }

    public IndexDefinition NumberOfPods(int pods)
    {
        this.Pods = pods;
        return this;
    }

    public IndexDefinition NumberOfReplicas(int replicas)
    {
        this.Replicas = replicas;
        return this;
    }

    public IndexDefinition WithPodType(PodType podType)
    {
        this.PodType = podType;
        return this;
    }

    public IndexDefinition WithMetadataIndex(MetadataIndexConfig? config = default)
    {
        this.MetadataConfig = config;
        return this;
    }

    public IndexDefinition FromSourceCollection(string sourceCollection)
    {
        this.SourceCollection = sourceCollection;
        return this;
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage? request = HttpRequest.CreatePostRequest("/databases", this);
        return request;
    }

    public static IndexDefinition Default(string? name = default)
    {
        string? indexName = name ?? "sk-index";
        return Create(indexName)
            .WithDimension(1536)
            .WithMetric(IndexMetric.Cosine)
            .NumberOfPods(1)
            .NumberOfReplicas(1)
            .WithPodType(PodType.P1X1)
            .WithMetadataIndex(MetadataIndexConfig.Default);
    }

    /// <summary>
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        StringBuilder sb = new();
        sb.Append("IndexDefinition {\n");
        sb.Append("  Name: ").Append(this.Name).Append('\n');
        sb.Append("  Dimension: ").Append(this.Dimension).Append('\n');
        sb.Append("  Metric: ").Append(this.Metric).Append('\n');
        sb.Append("  Pods: ").Append(this.Pods).Append('\n');
        sb.Append("  Shards: ").Append(this.Shards).Append('\n');
        sb.Append("  Replicas: ").Append(this.Replicas).Append('\n');
        sb.Append("  PodType: ").Append(this.PodType).Append('\n');
        sb.Append("  MetadataConfig: ").Append(this.MetadataConfig).Append('\n');
        sb.Append("  SourceCollection: ").Append(this.SourceCollection).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="IndexDefinition" /> class.
    /// </summary>
    [JsonConstructor]
    public IndexDefinition(string name)
    {
        this.Name = name;
    }

}
