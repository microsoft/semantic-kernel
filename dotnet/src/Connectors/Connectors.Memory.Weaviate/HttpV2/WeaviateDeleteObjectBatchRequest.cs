// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateDeleteObjectBatchRequest(WeaviateQueryMatch match)
{
    private const string ApiRoute = "batch/objects";

    [JsonPropertyName("match")]
    public WeaviateQueryMatch Match { get; set; } = match;

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateDeleteRequest(ApiRoute, this);
    }
}
