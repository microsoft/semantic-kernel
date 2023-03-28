// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

internal class VectorSettings : IValidatable
{
    [JsonPropertyName("size")]
    internal int Size { get; set; }

    [JsonPropertyName("distance")]
    internal string DistanceAsString
    {
        get { return QdrantDistanceUtils.DistanceTypeToString(this.DistanceType); }
        set { this.DistanceType = QdrantDistanceUtils.DistanceStringToType(value); }
    }

    [JsonIgnore]
    internal QdrantDistanceType DistanceType { get; set; }

    public void Validate()
    {
        Verify.True(this.Size > 0, "The vector size must be greater than zero");
        Verify.NotNull(this.DistanceType, "The distance type has not been defined");
        Verify.True(
            this.DistanceType is QdrantDistanceType.Cosine or QdrantDistanceType.DotProduct or QdrantDistanceType.Euclidean or QdrantDistanceType.Manhattan,
            $"Distance type {this.DistanceType:G} not supported.");
    }
}
