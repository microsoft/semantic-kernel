// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes: Used for Json Deserialization
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
internal sealed class GetVectorsResponse : QdrantResponse
{
    internal sealed class Record
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("payload")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public Dictionary<string, object>? Payload { get; set; }

        [JsonPropertyName("vector")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public ReadOnlyMemory<float>? Vector { get; set; }

        [JsonConstructor]
        public Record(string id, Dictionary<string, object>? payload, ReadOnlyMemory<float>? vector)
        {
            this.Id = id;
            this.Payload = payload;
            this.Vector = vector;
        }
    }

    /// <summary>
    /// Array of vectors and their associated metadata
    /// </summary>
    [JsonPropertyName("result")]
    public IEnumerable<Record> Result { get; set; } = [];
}
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
