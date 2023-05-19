// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

internal sealed class ListPointsResponse : QdrantResponse
{
    [JsonPropertyName("result")]
    public PointsResult? Result { get; set; }

    internal class PointsResult
    {
        [JsonPropertyName("points")]
        public IEnumerable<QdrantPointRecord>? Points { get; set; }
    }
}
