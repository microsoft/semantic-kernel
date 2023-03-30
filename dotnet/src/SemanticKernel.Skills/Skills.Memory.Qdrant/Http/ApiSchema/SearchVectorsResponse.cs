// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.Http.ApiSchema;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes: Used for Json Deserialization
internal class SearchVectorsResponse<TEmbedding> : QdrantResponse
    where TEmbedding : unmanaged
{
    internal class ScoredPoint
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("version")]
        public int Version { get; set; }

        [JsonPropertyName("score")]
        public double? Score { get; set; }

        [JsonPropertyName("payload")]
        public Dictionary<string, object> Payload { get; set; }

        [JsonPropertyName("vector")]
        public TEmbedding[] Vector { get; set; } = Array.Empty<TEmbedding>();

        [JsonConstructor]
        public ScoredPoint(string id, double? score, Dictionary<string, object> payload, TEmbedding[] vector)
        {
            this.Id = id;
            this.Score = score;
            this.Payload = payload;
            this.Vector = vector;
        }
    }

    [JsonPropertyName("result")]
    public IEnumerable<ScoredPoint> Results { get; set; }

    [JsonConstructor]
    public SearchVectorsResponse(IEnumerable<ScoredPoint> results)
    {
        this.Results = results;
    }

    #region private ================================================================================

    private SearchVectorsResponse()
    {
        this.Results = new List<ScoredPoint>();
    }

    #endregion
}
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
