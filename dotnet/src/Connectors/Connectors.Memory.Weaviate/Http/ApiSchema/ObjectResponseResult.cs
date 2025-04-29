// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

// ReSharper disable once ClassNeverInstantiated.Global
#pragma warning disable CA1812 // 'ObjectResponseResult' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class ObjectResponseResult
#pragma warning restore CA1812 // 'ObjectResponseResult' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
{
    public JsonObject? Errors { get; set; }
    public string? Status { get; set; }
}
