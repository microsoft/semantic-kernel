// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class GetSchemaRequest
{
    public static GetSchemaRequest Create()
    {
        return new();
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateGetRequest("schema");
    }
}
