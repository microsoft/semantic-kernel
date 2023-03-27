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

}

internal class PointParams
{
    [JsonPropertyName("offset")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    internal int? Offset { get; set; }

    [JsonPropertyName("limit")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    internal int? Limit { get; set; }

    [JsonPropertyName("with_payload")]
    internal bool WithPayload { get; set; }

    [JsonPropertyName("with_vector")]
    internal bool WithVector { get; set; }
}

internal class PointFilter
{
    [JsonPropertyName("key")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    internal string? PayloadKey { get; set; }

    [JsonPropertyName("match")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    internal Dictionary<string, string>? value { get; set; }

    [JsonPropertyName("range")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    internal PointRange? Range { get; set; }
}

internal class PointRange
{
    [JsonPropertyName("lt")]
    internal double LessThan { get; set; }
    
    [JsonPropertyName("gt")]
    internal double GreaterThan { get; set; }
    
    [JsonPropertyName("gte")]
    internal double GreaterThanEqual { get; set; }

    [JsonPropertyName("lte")]
    internal double LessThanEqual { get; set; }

}

internal class PointUpsertParams
{
    [JsonPropertyName("points")]
    internal List<Points>? PointData { get; set; }
}

internal class PointDeleteParams
{
    [JsonPropertyName("points")]
    internal int[]? PointIds { get; set; }
}