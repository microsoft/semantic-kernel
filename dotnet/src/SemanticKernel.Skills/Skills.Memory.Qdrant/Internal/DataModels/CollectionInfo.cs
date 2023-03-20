// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
internal class CollectionInfo
{
    [JsonPropertyName("status")]
    internal string CollectionStatus { get; set; } = string.Empty;

    [JsonPropertyName("optimizer_status")]
    internal string OptimizerStatus { get; set; } = string.Empty;

    [JsonPropertyName("vectors_count")]
    internal int VectorsCount { get; set; }

    [JsonPropertyName("indexed_vectors_count")]
    internal int IndexedVectorsCount { get; set; }

    [JsonPropertyName("points_count")]
    internal int PointsCount { get; set; }

    [JsonPropertyName("segments_count")]
    internal int SegmentsCount { get; set; }

}


