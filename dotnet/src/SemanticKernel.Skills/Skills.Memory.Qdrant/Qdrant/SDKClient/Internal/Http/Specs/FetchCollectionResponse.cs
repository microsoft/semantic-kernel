// Copyright (c) Microsoft. All rights reserved.

using System;
using Newtonsoft.Json.Linq;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.HttpSchema;

internal class FetchCollectionResponse
{
    internal string Status { get; set; } = string.Empty;
    internal string OptimizerStatus { get; set; } = string.Empty;
    internal int VectorsCount { get; set; }
    internal int IndexedVectorsCount { get; set; }
    internal int PointsCount { get; set; }
    internal int SegmentsCount { get; set; }
    internal int VectorsSize { get; set; }
    internal string Distance { get; set; } = string.Empty;

    internal FetchCollectionResponse(string json)
    {
        // TODO: Replace with a System.Text.Json implementation
        dynamic value = JObject.Parse(json);
        FromDynamic(value);
    }

    #region private ================================================================================

    private void FromDynamic(dynamic data)
    {
        if (data == null)
        {
            throw new ArgumentNullException(nameof(data), "Cannot extract a collection object from NULL");
        }

        this.Status = data.result.status;
        this.OptimizerStatus = ((string)data.result.optimizer_status).ToUpperInvariant();
        this.VectorsCount = data.result.vectors_count;
        this.IndexedVectorsCount = data.result.indexed_vectors_count;
        this.PointsCount = data.result.points_count;
        this.SegmentsCount = data.result.segments_count;
        this.VectorsSize = data.result.config.@params.vectors.size;
        this.Distance = data.result.config.@params.vectors.distance;
    }

    #endregion
}
