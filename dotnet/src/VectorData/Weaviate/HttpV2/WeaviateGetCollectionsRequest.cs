// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateGetCollectionsRequest
{
    private const string ApiRoute = "schema";

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateGetRequest(ApiRoute);
    }
}
