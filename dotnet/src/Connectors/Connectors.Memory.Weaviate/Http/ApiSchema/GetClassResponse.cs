// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

internal sealed class GetClassResponse
{
    public string? Class { get; set; }
    public string? Description { get; set; }
}
