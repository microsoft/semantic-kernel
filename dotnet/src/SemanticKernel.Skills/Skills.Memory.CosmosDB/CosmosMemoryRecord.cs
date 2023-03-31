// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;

namespace Skills.Memory.CosmosDB;

[JsonObject(NamingStrategyType = typeof(CamelCaseNamingStrategy))]
public class CosmosMemoryRecord : IEmbeddingWithMetadata<float>
{
    public string Id { get; set; } = string.Empty;

    public string CollectionId { get; set; } = string.Empty;

    public DateTimeOffset? Timestamp { get; set; }

    [JsonIgnore]
    public Embedding<float> Embedding { get; set; } = new();

    public string EmbeddingString { get; set; } = string.Empty;

    /// <summary>
    /// Metadata associated with a Semantic Kernel memory.
    /// </summary>
    [JsonIgnore]
    public MemoryRecordMetadata? Metadata { get; set; }

    public string MetadataString { get; set; } = string.Empty;

    public string GetSerializedMetadata()
    {
        return JsonConvert.SerializeObject(this.Metadata);
    }
}

