// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate.ModelV2;

internal sealed class WeaviateQueryMatchOperand
{
    [JsonPropertyName("operator")]
    public string? Operator { get; set; }

    [JsonPropertyName("path")]
    public List<string> Path { get; set; } = [];

    [JsonPropertyName("valueStringArray")]
    public List<string> Values { get; set; } = [];
}
