// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

internal sealed class GetCollectionsRequest
{
    /// <summary>
    /// Name of the collection to request vectors from
    /// </summary>
    [JsonIgnore]
    public string Collection { get; set; }

    public static GetCollectionsRequest Create(string collectionName)
    {
        return new GetCollectionsRequest(collectionName);
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateGetRequest($"collections/{this.Collection}");
    }

    #region private ================================================================================

    private GetCollectionsRequest(string collectionName)
    {
        this.Collection = collectionName;
    }

    #endregion
}
