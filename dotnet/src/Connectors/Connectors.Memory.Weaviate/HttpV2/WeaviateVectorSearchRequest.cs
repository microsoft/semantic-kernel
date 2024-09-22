// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateVectorSearchRequest(string query)
{
    private const string ApiRoute = "graphql";

    [JsonPropertyName("query")]
    public string Query { get; set; } = query;

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(ApiRoute, this);
    }
}
