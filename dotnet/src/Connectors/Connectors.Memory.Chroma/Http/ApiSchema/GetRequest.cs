// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

internal sealed class GetRequest
{
    [JsonPropertyName("ids")]
    public string[]? Ids { get; set; }

    [JsonPropertyName("where")]
    public Dictionary<string, object>? Where { get; set; }

    [JsonIgnore]
    public string Sort { get; set; } = String.Empty;

    [JsonIgnore]
    public int? Limit { get; set; }

    [JsonIgnore]
    public int? Offset { get; set; }

    [JsonPropertyName("where")]
    public Dictionary<string, object>? WhereDocument { get; set; }

    [JsonInclude]
    public string[]? Include { get; set; }
}