// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.Http.ApiSchema;

internal class UpsertVectorRequest<TEmbedding>
    where TEmbedding : unmanaged
{
    public static UpsertVectorRequest<TEmbedding> Create(string collectionName)
    {
        return new UpsertVectorRequest<TEmbedding>(collectionName);
    }

    public UpsertVectorRequest<TEmbedding> UpsertVector(string pointId, QdrantVectorRecord<TEmbedding> vectorRecord)
    {
        this.Batch.Ids.Add(pointId);
        this.Batch.Vectors.Add(vectorRecord.Embedding.Vector.ToArray());
        this.Batch.Payloads.Add(vectorRecord.Payload);
        return this;
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePutRequest(
            $"collections/{this.Collection}/points?wait=true",
            payload: this);
    }

    [JsonIgnore]
    public string Collection { get; set; }

    [JsonPropertyName("batch")]
    public BatchRequest Batch { get; set; }

    internal class BatchRequest
    {
        [JsonPropertyName("ids")]
        public IList<string> Ids { get; set; }

        [JsonPropertyName("vectors")]
        public IList<TEmbedding[]> Vectors { get; set; }

        [JsonPropertyName("payloads")]
        public IList<Dictionary<string, object>> Payloads { get; set; }

        internal BatchRequest()
        {
            this.Ids = new List<string>();
            this.Vectors = new List<TEmbedding[]>();
            this.Payloads = new List<Dictionary<string, object>>();
        }
    }

    #region private ================================================================================

    private UpsertVectorRequest(string collectionName)
    {
        this.Collection = collectionName;
        this.Batch = new BatchRequest();
    }

    #endregion
}
