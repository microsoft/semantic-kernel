// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Experimental("SKEXP0020")]
internal sealed class DeleteObjectRequest
{
    public string? Class { get; set; }
    public string? Id { get; set; }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateDeleteRequest($"objects/{this.Class}/{this.Id}");
    }
}
