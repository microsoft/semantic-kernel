// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class DeleteObjectRequest
{
    public string? Class { get; set; }
    public string? Id { get; set; }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateDeleteRequest($"objects/{this.Class}/{this.Id}");
    }
}
