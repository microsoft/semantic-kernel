// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

internal sealed class ListPointsRequest : IValidatable
{
    #region private

    private readonly string _collectionName;

    private int _offset;

    private int _limit;

    private ListPointsRequest(string collectionName)
    {
        this._collectionName = collectionName;
    }

    #endregion private

    public static ListPointsRequest Create(string collectionName)
    {
        return new ListPointsRequest(collectionName);
    }

    public ListPointsRequest Offset(int offset)
    {
        this._offset = offset;
        return this;
    }

    public ListPointsRequest Limit(int limit)
    {
        this._limit = limit;
        return this;
    }

    public HttpRequestMessage Build()
    {
        this.Validate();
        return HttpRequest.CreatePostRequest(
            $"collections/{this._collectionName}/points/scroll",
            payload: this);
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
    }
}
