
// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

internal sealed class QueryResponse
{
    public float[][]? Embeddings { get; set; }

    public Dictionary<string, object>[]? Metadatas { get; set; }

    public string[]? Documents { get; set; }

    public string[]? Ids { get; set; }

    public float[]? Distances { get; set; }

    public string Name {get; set; } = String.Empty;
}