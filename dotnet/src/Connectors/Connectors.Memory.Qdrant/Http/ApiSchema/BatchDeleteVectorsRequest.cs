// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

internal sealed class BatchDeleteVectorsRequest
{
    [JsonPropertyName("keys")]
    public HashSet<string> Ids { get; set; }

    public static BatchDeleteVectorsRequest DeleteFrom(string collectionName)
    {
        return new BatchDeleteVectorsRequest(collectionName);
    }

    public BatchDeleteVectorsRequest DeleteVectors(string[] keys)
    {
        Verify.NotNull(keys, nameof(keys));
        foreach (var item in keys)
        {
            Verify.NotNullOrWhiteSpace(item);
            this.Ids.Add(item);
        }
        return this;
    }

    public HttpRequestMessage Build()
    {
        Verify.NotNullOrWhiteSpace(this._collectionName, nameof(this._collectionName));

        return HttpRequest.CreatePostRequest(
            $"collections/{this._collectionName}/points/payload/delete",
            payload: this);
    }

    #region private ================================================================================

    private readonly string _collectionName;

    private BatchDeleteVectorsRequest(string collectionName)
    {
        this.Ids = [];
        this._collectionName = collectionName;
    }

    #endregion
}
