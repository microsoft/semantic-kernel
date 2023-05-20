// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

// ReSharper disable once ClassNeverInstantiated.Global
internal sealed class ObjectResponseResult
{
    public JsonObject? Errors { get; set; } // TODO? should this be an object?
    public string? Status { get; set; }
}
