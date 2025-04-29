// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
internal sealed class UpsertVectorRequest
{
    public static UpsertVectorRequest Create(string collectionName)
    {
        return new UpsertVectorRequest(collectionName);
    }

    public UpsertVectorRequest UpsertVector(QdrantVectorRecord vectorRecord)
    {
        this.Batch.Ids.Add(vectorRecord.PointId);
        this.Batch.Vectors.Add(vectorRecord.Embedding);
        this.Batch.Payloads.Add(vectorRecord.Payload);
        return this;
    }

    public UpsertVectorRequest UpsertRange(IEnumerable<QdrantVectorRecord> vectorRecords)
    {
        foreach (var vectorRecord in vectorRecords)
        {
            this.UpsertVector(vectorRecord);
        }

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

    internal sealed class BatchRequest
    {
        [JsonPropertyName("ids")]
        public IList<string> Ids { get; set; }

        [JsonPropertyName("vectors")]
        public IList<ReadOnlyMemory<float>> Vectors { get; set; }

        [JsonPropertyName("payloads")]
        public IList<Dictionary<string, object>> Payloads { get; set; }

        internal BatchRequest()
        {
            this.Ids = [];
            this.Vectors = [];
            this.Payloads = [];
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
