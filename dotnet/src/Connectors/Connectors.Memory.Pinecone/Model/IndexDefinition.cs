// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// Used to create a new index.
/// See https://docs.pinecone.io/reference/create_index
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
    /// The index metric to use for similarity search.
    /// </summary>
    [JsonPropertyName("metric")]
    public IndexMetric Metric { get; set; } = IndexMetric.Cosine;

    /// <summary>
    /// The type of pod to use for the index.
    /// </summary>
    [JsonPropertyName("pod_type")]
    public PodType PodType { get; set; } = PodType.P1X1;

    /// <summary>
    /// The number of dimensions in the vector representation
    /// </summary>
    [JsonPropertyName("dimension")]
    public int Dimension { get; set; } = 1536;

    /// <summary>
    /// The number of pods for the index to use,including replicas.
    /// </summary>
    [JsonPropertyName("pods")]
    public int Pods { get; set; } = 1;

    /// <summary>
    /// The number of replicas. Replicas duplicate your index. They provide higher availability and throughput.
    /// </summary>
    [JsonPropertyName("replicas")]
    public int Replicas { get; set; }

    /// <summary>
    /// The numbers of shards for the index to use.
    /// </summary>
    [JsonPropertyName("shards")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public int? Shards { get; set; }

    /// <summary>
    /// The metadata index configuration.
    /// </summary>
    /// <see cref="MetadataIndexConfig.Default"/>
    [JsonPropertyName("metadata_config")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public MetadataIndexConfig? MetadataConfig { get; set; }

    /// <summary>
    /// The unique name of a collection.
    /// </summary>
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
        HttpRequestMessage request = HttpRequest.CreatePostRequest("/databases", this);

        request.Headers.Add("accept", "text/plain");

        return request;
    }

    public static IndexDefinition Default(string? name = default)
    {
        string indexName = name ?? PineconeUtils.DefaultIndexName;

        return Create(indexName)
            .WithDimension(PineconeUtils.DefaultDimension)
            .WithMetric(PineconeUtils.DefaultIndexMetric)
            .NumberOfPods(1)
            .NumberOfReplicas(1)
            .WithPodType(PineconeUtils.DefaultPodType)
            .WithMetadataIndex(MetadataIndexConfig.Default);
    }

    /// <inheritdoc />
    public override string ToString()
    {
        StringBuilder builder = new();

        builder.Append("Configuration :");
        builder.AppendLine($"Name: {this.Name}, ");
        builder.AppendLine($"Dimension: {this.Dimension}, ");
        builder.AppendLine($"Metric: {this.Metric}, ");
        builder.AppendLine($"Pods: {this.Pods}, ");
        builder.AppendLine($"Replicas: {this.Replicas}, ");
        builder.AppendLine($"PodType: {this.PodType}, ");

        if (this.MetadataConfig != null)
        {
            builder.AppendLine($"MetaIndex: {string.Join(",", this.MetadataConfig)}, ");
        }

        if (this.SourceCollection != null)
        {
            builder.AppendLine($"SourceCollection: {this.SourceCollection}, ");
        }

        return builder.ToString();
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
