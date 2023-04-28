// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

/// <summary>
/// ListIndexesRequest
/// See https://docs.pinecone.io/reference/list_indexes 
/// </summary>
internal sealed class ListIndexesRequest
{
    public static ListIndexesRequest Create()
    {
        return new ListIndexesRequest();
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage? request = HttpRequest.CreateGetRequest("/databases");
        return request;
    }
}
