// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateDeleteObjectBatchRequest
{
    private const string ApiRoute = "batch/objects";

    [JsonConstructor]
    public WeaviateDeleteObjectBatchRequest() { }

    public WeaviateDeleteObjectBatchRequest(WeaviateQueryMatch match)
    {
        this.Match = match;
    }

    [JsonPropertyName("match")]
    public WeaviateQueryMatch? Match { get; set; }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateDeleteRequest(ApiRoute, this);
    }
}
