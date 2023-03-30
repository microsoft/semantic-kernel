// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.Http.ApiSchema;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes: Used for Json Deserialization
internal class GetVectorsResponse<TEmbedding> : QdrantResponse
    where TEmbedding : unmanaged
{
    internal class Record
    {
        [JsonPropertyName("id")]
        public Guid Id { get; set; }

        [JsonPropertyName("payload")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public Dictionary<string, object>? Payload { get; set; }

        [JsonPropertyName("vector")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public TEmbedding[]? Vector { get; set; }
    }

    /// <summary>
    /// Array of vectors and their associated metadata
    /// </summary>
    [JsonPropertyName("result")]
    public IEnumerable<Record> Result { get; set; } = new List<Record>();
}
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
