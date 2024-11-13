// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Experimental("SKEXP0020")]
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
