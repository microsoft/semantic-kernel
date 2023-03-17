// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Skills.Memory.VectorDB.Internal.Diagnostics;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal class FetchCollectionRequest : IValidatable
{
    public static FetchCollectionRequest Fetch(string collectionName)
    {
        return new FetchCollectionRequest(collectionName);
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
    }

    public HttpRequestMessage Build()
    {
        this.Validate();
        return HttpRequest.CreateGetRequest($"collections/{this._collectionName}");
    }

    #region private ================================================================================

    private readonly string _collectionName;

    private FetchCollectionRequest(string collectionName)
    {
        this._collectionName = collectionName;
    }

    #endregion
}
