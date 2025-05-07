// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// ListIndexesRequest
/// See https://docs.pinecone.io/reference/list_indexes
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class ListIndexesRequest
{
    public static ListIndexesRequest Create()
    {
        return new ListIndexesRequest();
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage? request = HttpRequest.CreateGetRequest("/databases");

        request.Headers.Add("accept", "application/json; charset=utf-8");

        return request;
    }
}
