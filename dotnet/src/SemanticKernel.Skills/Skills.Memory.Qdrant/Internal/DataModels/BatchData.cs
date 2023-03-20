// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

internal class BatchData<TEmbedding> : IValidatable
where TEmbedding : unmanaged
{
    [JsonPropertyName("ids")]
    internal List<string> Ids { get; set; }

    [JsonPropertyName("vectors")]
    internal List<TEmbedding[]> Vectors { get; set; }

    [JsonPropertyName("payloads")]
    internal List<object> Payloads { get; set; }

    internal BatchData()
    {
        this.Ids = new();
        this.Vectors = new();
        this.Payloads = new();
    }

    public void Validate()
    {
        Verify.True(this.Ids.Count == this.Vectors.Count && this.Vectors.Count == this.Payloads.Count,
            "The batch content is not consistent");
    }
}
