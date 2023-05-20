// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

internal sealed class GraphResponse
{
    public JsonObject Data { get; set; }
    public GraphError[] Errors { get; set; }
}