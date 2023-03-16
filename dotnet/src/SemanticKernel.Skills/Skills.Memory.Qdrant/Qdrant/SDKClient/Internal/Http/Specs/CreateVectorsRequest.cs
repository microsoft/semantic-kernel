// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.HttpSchema;

internal class CreateVectorsRequest : IValidatable
{
    public static CreateVectorsRequest CreateIn(string collectionName)
    {
        return new CreateVectorsRequest(collectionName);
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
        this.Batch.Validate();
    }

    public CreateVectorsRequest UpsertVector(string pointId, DataEntry<VectorRecordData<float>> vector)
    {
        this.Batch.Ids.Add(pointId);
        this.Batch.Vectors.Add(vector.Value!.Embedding.Vector.ToArray());
        this.Batch.Payloads.Add(PointPayloadDataMapper.PreparePointPayload(vector));
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
        this.Batch = new BatchRequest();
    }

    [JsonPropertyName("batch")]
    private BatchRequest Batch { get; set; }

    private class BatchRequest : IValidatable
    {
        [JsonPropertyName("ids")]
        internal List<string> Ids { get; set; }

        [JsonPropertyName("vectors")]
        internal List<float[]> Vectors { get; set; }

        [JsonPropertyName("payloads")]
        internal List<object> Payloads { get; set; }

        internal BatchRequest()
        {
            this.Ids = new();
            this.Vectors = new();
            this.Payloads = new();
        }

        public void Validate()
        {
            Verify.True(this.Ids.Count == this.Vectors.Count && this.Vectors.Count == this.Payloads.Count,
                "The batch content is not consistent");
        }
    }

    #endregion
}
