﻿// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// ListIndexesRequest
/// See https://docs.pinecone.io/reference/list_indexes
/// </summary>
[Experimental("SKEXP0020")]
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
