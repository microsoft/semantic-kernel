// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal class WeaviateOperationResultErrors
{
    [JsonPropertyName("error")]
    public List<WeaviateOperationResultError>? Errors { get; set; }
}
