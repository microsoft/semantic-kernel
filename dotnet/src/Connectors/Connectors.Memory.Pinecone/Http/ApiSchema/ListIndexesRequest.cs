// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// ListIndexesRequest
/// See https://docs.pinecone.io/reference/list_indexes
/// </summary>
internal static class ListIndexesRequest
{
    public static HttpRequestMessage Build()
    {
        HttpRequestMessage request = HttpRequest.CreateGetRequest("/databases");

        request.Headers.Add("accept", "application/json; charset=utf-8");

        return request;
    }
}
