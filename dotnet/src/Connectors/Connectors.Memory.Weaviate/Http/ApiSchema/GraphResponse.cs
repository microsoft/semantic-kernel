// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable CA1812 // 'GraphResponse' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class GraphResponse
#pragma warning restore CA1812 // 'GraphResponse' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
{
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
    public JsonObject Data { get; set; }
    public GraphError[] Errors { get; set; }
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
}
