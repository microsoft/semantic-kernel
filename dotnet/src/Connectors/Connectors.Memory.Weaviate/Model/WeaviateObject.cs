// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal class WeaviateObject
{
    public string? Id { get; set; }
    public string? Class { get; set; }
    public Dictionary<string, object>? Properties { get; set; }
    public ReadOnlyMemory<float> Vector { get; set; }
}
