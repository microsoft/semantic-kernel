// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

internal sealed class AddRequest
{

    /// <summary>
    /// The name of the collection to create
    /// </summary>
    [JsonPropertyName("embeddings")]
    public float[]? Embeddings { get; set; }

    [JsonPropertyName("metadata")]
    public object[]? Metadatas { get; set; }

    [JsonPropertyName("documents")]
    public string[]? Documents { get; set; }

    [JsonPropertyName("ids")]
    public string[]? Ids { get; set; }
}