// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateDeleteCollectionSchemaRequest(string collectionName)
{
    private const string ApiRoute = "schema";

    [JsonIgnore]
    public string CollectionName { get; set; } = collectionName;

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateDeleteRequest($"{ApiRoute}/{this.CollectionName}");
    }
}
