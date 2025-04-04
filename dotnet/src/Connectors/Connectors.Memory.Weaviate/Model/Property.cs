// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class Property
{
    public string? Name { get; set; }
    public string[]? DataType { get; set; }
    public bool IndexInverted { get; set; }
}
