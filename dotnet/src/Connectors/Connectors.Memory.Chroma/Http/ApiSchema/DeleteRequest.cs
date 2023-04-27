// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

internal sealed class DeleteRequest
{
    [JsonPropertyName("ids")]
    public string[]? Ids { get; set; }

    [JsonPropertyName("where")]
    public Dictionary<string, object>? Where { get; set; }

     [JsonPropertyName("wheredocument")]
    public Dictionary<string, object>? WhereDocument { get; set; }
}