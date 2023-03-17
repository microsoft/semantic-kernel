// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal class CreateVectorsRequest<TEmbedding> : IValidatable
where TEmbedding : unmanaged
{
    public static CreateVectorsRequest<TEmbedding> CreateIn(string collectionName)
    {
        return new CreateVectorsRequest<TEmbedding>(collectionName);
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
        this.Batch.Validate();
    }

    public CreateVectorsRequest<TEmbedding> UpsertVector(string pointId, QdrantVectorRecord<TEmbedding> vectorRecord)
    {
        this.Batch.Ids.Add(pointId);
        this.Batch.Vectors.Add(vectorRecord.Embedding.Vector.ToArray());
        this.Batch.Payloads.Add(JsonSerializer.Deserialize<List<object>>(vectorRecord.JsonSerializeMetadata()));
        return this;
    }

    public HttpRequestMessage Build()
    {
        this.Validate();
        return HttpRequest.CreatePutRequest(
            $"collections/{this._collectionName}/points?wait=true",
            payload: this);
    }

    #region private ================================================================================

    private readonly string _collectionName;

    private CreateVectorsRequest(string collectionName)
    {
        this._collectionName = collectionName;
        this.Batch = new BatchData<TEmbedding>();
    }

    [JsonPropertyName("batch")]
    private BatchData<TEmbedding> Batch { get; set; }

    #endregion
}
