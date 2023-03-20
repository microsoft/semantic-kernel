// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

internal class Points
{
    [JsonPropertyName("id")]
    internal string? VectorId { get; set; }

    [JsonPropertyName("payload")]
    internal Dictionary<string, object>? Payload { get; set; }

    [JsonPropertyName("vector")]
    internal float[]? Vector { get; set; }

    [JsonPropertyName("status")]
    internal string? Status { get; set; }

}
