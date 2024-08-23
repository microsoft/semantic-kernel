// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate.ModelV2;

internal sealed class WeaviateQueryMatchWhereClause
{
    [JsonPropertyName("operands")]
    public List<WeaviateQueryMatchOperand> Operands { get; set; } = [];
}
