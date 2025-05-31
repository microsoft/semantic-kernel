// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateOperationResultError
{
    [JsonPropertyName("message")]
    public string? Message { get; set; }
}
