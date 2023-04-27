// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

internal sealed class QueryRequest
{
    public float[][]? QueryEmbeddings { get; set; }

    public int NResults { get; set; }

    public Dictionary<string, object>? Where { get; set; }

    public Dictionary<string, object>? WhereDocument { get; set; }

    public string[]? Include { get; set; }
}
        