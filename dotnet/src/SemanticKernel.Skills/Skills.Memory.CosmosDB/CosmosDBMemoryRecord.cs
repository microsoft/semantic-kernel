// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;

namespace Skills.Memory.CosmosDB;

/// <summary>
/// A CosmosDB memory record.
/// </summary>
[JsonObject(NamingStrategyType = typeof(CamelCaseNamingStrategy))]
public class CosmosDBMemoryRecord : IEmbeddingWithMetadata<float>
{
    /// <summary>
    /// Unique identifier of the memory record.
    /// </summary>
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Unique identifier of the collection.
    /// </summary>
    public string CollectionId { get; set; } = string.Empty;

    /// <summary>
    /// Optional timestamp.
    /// </summary>
    public DateTimeOffset? Timestamp { get; set; }

    /// <summary>
    /// The embedding data.
    /// </summary>
    [JsonIgnore]
    public Embedding<float> Embedding { get; set; } = new();

    /// <summary>
    /// The embedding data as a string.
    /// </summary>
    public string EmbeddingString { get; set; } = string.Empty;

    /// <summary>
    /// Metadata associated with a Semantic Kernel memory.
    /// </summary>
    [JsonIgnore]
    public MemoryRecordMetadata? Metadata { get; set; }

    /// <summary>
    /// Metadata as a string.
    /// </summary>
    public string MetadataString { get; set; } = string.Empty;

    /// <summary>
    /// Metadata serialized as a JSON string.
    /// </summary>
    public string GetSerializedMetadata()
    {
        return JsonConvert.SerializeObject(this.Metadata);
    }
}

