﻿// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Get information about an index.
/// See https://docs.pinecone.io/reference/describe_index
/// </summary>
[Experimental("SKEXP0020")]
internal sealed class DescribeIndexRequest
{
    /// <summary>
    /// The unique name of an index.
    /// </summary>
    public string IndexName { get; }

    public static DescribeIndexRequest Create(string indexName)
    {
        return new DescribeIndexRequest(indexName);
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage? request = HttpRequest.CreateGetRequest(
            $"/databases/{this.IndexName}");

        request.Headers.Add("accept", "application/json");

        return request;
    }

    #region private ================================================================================

    private DescribeIndexRequest(string indexName)
    {
        this.IndexName = indexName;
    }

    #endregion
}
