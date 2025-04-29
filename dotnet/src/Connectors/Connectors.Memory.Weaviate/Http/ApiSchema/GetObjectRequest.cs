// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class GetObjectRequest
{
    public string? Id { get; set; }
    public string[]? Additional { get; set; }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateGetRequest($"objects/{this.Id}{(this.Additional is null ? string.Empty : $"?include={string.Join(",", this.Additional)}")}");
    }
}
