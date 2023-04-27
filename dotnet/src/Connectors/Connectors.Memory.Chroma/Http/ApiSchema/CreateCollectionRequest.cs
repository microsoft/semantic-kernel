
// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

internal sealed class CreateCollectionRequest
{
    /// <summary>
    /// The name of the collection to create
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = String.Empty;

    /// <summary>
    /// The dictionary of the metadata associated with collection
    /// </summary>
    [JsonPropertyName("metatdata")]
    public Dictionary<string, object>? Metadata { get; set; }
}
