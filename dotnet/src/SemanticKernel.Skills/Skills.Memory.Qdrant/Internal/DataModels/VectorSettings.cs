// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
internal class VectorSettings : IValidatable
    {
        [JsonPropertyName("size")]
        internal int Size { get; set; }

        [JsonPropertyName("distance")]
        internal string DistanceAsString
        {
            get { return DistanceTypeToString(this.DistanceType); }
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

        private static string DistanceTypeToString(QdrantDistanceType x)
        {
            return x switch
            {
                QdrantDistanceType.Cosine => "Cosine",
                QdrantDistanceType.DotProduct => "DotProduct",
                QdrantDistanceType.Euclidean => "Euclidean",
                QdrantDistanceType.Manhattan => "Manhattan",
                _ => throw new NotSupportedException($"Distance type {Enum.GetName(typeof(QdrantDistanceType), x)} not supported")
            };
        }
    }