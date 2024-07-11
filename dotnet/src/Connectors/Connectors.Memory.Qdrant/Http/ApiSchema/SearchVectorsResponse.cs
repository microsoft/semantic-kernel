// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes: Used for Json Deserialization
internal sealed class SearchVectorsResponse : QdrantResponse
{
    internal sealed class ScoredPoint
    {
        [JsonPropertyName("id")]
        [JsonConverter(typeof(NumberToStringConverter))]
        public string Id { get; }

        [JsonPropertyName("version")]
        public int Version { get; set; }

        [JsonPropertyName("score")]
        public double? Score { get; }

        [JsonPropertyName("payload")]
        public Dictionary<string, object> Payload { get; set; }

        [JsonPropertyName("vector")]
        [JsonConverter(typeof(ReadOnlyMemoryConverter))]
        public ReadOnlyMemory<float> Vector { get; }

        [JsonConstructor]
        public ScoredPoint(string id, double? score, Dictionary<string, object> payload, ReadOnlyMemory<float> vector)
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
