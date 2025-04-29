// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Used to create a new index.
/// See https://docs.pinecone.io/reference/create_index
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
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
    /// The number of pods for the index to use, including replicas.
    /// </summary>
    [JsonPropertyName("pods")]
    public int Pods { get; set; } = 1;

    /// <summary>
    /// The number of replicas. Replicas duplicate index. They provide higher availability and throughput.
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

    /// <summary>
    /// Initializes a new instance of the <see cref="IndexDefinition" /> class.
    /// </summary>
    /// <param name="name">The unique name of an index.</param>
    public static IndexDefinition Create(string name)
    {
        return new IndexDefinition(name);
    }

    /// <summary>
    /// Sets dimension for <see cref="IndexDefinition"/> instance.
    /// </summary>
    /// <param name="dimension">The number of dimensions in the vector representation.</param>
    public IndexDefinition WithDimension(int dimension)
    {
        this.Dimension = dimension;
        return this;
    }

    /// <summary>
    /// Sets metric for <see cref="IndexDefinition"/> instance.
    /// </summary>
    /// <param name="metric">The index metric to use for similarity search.</param>
    public IndexDefinition WithMetric(IndexMetric metric)
    {
        this.Metric = metric;
        return this;
    }

    /// <summary>
    /// Sets pods for <see cref="IndexDefinition"/> instance.
    /// </summary>
    /// <param name="pods">The number of pods for the index to use, including replicas.</param>
    public IndexDefinition NumberOfPods(int pods)
    {
        this.Pods = pods;
        return this;
    }

    /// <summary>
    /// Sets number of replicas for <see cref="IndexDefinition"/> instance.
    /// </summary>
    /// <param name="replicas">The number of replicas. Replicas duplicate index. They provide higher availability and throughput.</param>
    public IndexDefinition NumberOfReplicas(int replicas)
    {
        this.Replicas = replicas;
        return this;
    }

    /// <summary>
    /// Sets pod type for <see cref="IndexDefinition"/> instance.
    /// </summary>
    /// <param name="podType">The type of pod to use for the index.</param>
    public IndexDefinition WithPodType(PodType podType)
    {
        this.PodType = podType;
        return this;
    }

    /// <summary>
    /// Sets metadata index configuration for <see cref="IndexDefinition"/> instance.
    /// </summary>
    /// <param name="config">The metadata index configuration.</param>
    public IndexDefinition WithMetadataIndex(MetadataIndexConfig? config = default)
    {
        this.MetadataConfig = config;
        return this;
    }

    /// <summary>
    /// Sets source collection for <see cref="IndexDefinition"/> instance.
    /// </summary>
    /// <param name="sourceCollection">The unique name of a collection.</param>
    public IndexDefinition FromSourceCollection(string sourceCollection)
    {
        this.SourceCollection = sourceCollection;
        return this;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpRequestMessage" /> class with request body of <see cref="IndexDefinition"/>.
    /// </summary>
    public HttpRequestMessage Build()
    {
        HttpRequestMessage request = HttpRequest.CreatePostRequest("/databases", this);

        request.Headers.Add("accept", "text/plain");

        return request;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="IndexDefinition" /> class with default settings.
    /// </summary>
    /// <param name="name">The unique name of an index.</param>
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

        if (this.MetadataConfig is not null)
        {
            builder.AppendLine($"MetaIndex: {string.Join(",", this.MetadataConfig)}, ");
        }

        if (this.SourceCollection is not null)
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
