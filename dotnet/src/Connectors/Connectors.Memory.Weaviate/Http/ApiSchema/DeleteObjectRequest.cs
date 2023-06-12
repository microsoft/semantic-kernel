// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

internal sealed class DeleteObjectRequest
{
    public string? Class { get; set; }
    public string? Id { get; set; }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateDeleteRequest($"objects/{this.Class}/{this.Id}");
    }
}
