// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Deletes an index and all its data.
/// See https://docs.pinecone.io/reference/delete_index
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class DeleteIndexRequest
{
    public static DeleteIndexRequest Create(string indexName)
    {
        return new DeleteIndexRequest(indexName);
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage request = HttpRequest.CreateDeleteRequest(
            $"/databases/{this._indexName}");

        request.Headers.Add("accept", "text/plain");

        return request;
    }

    #region private ================================================================================

    private readonly string _indexName;

    private DeleteIndexRequest(string indexName)
    {
        this._indexName = indexName;
    }

    #endregion
}
