// Copyright (c) Microsoft. All rights reserved.

using System;
using Newtonsoft.Json.Linq;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClientanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Http.Specs;

internal class FetchCollectionResponse
{
    internal string Status { get; set; }
    internal string OptimizerStatus { get; set; }
    internal int VectorsCount { get; set; }
    internal int IndexedVectorsCount { get; set; }
    internal int PointsCount { get; set; }
    internal int SegmentsCount { get; set; }
    internal int VectorsSize { get; set; }
    internal string Distance { get; set; }

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

        try
        {
            this.Status = data.result.status;
            this.OptimizerStatus = ((string)data.result.optimizer_status).ToLowerInvariant();
            this.VectorsCount = data.result.vectors_count;
            this.IndexedVectorsCount = data.result.indexed_vectors_count;
            this.PointsCount = data.result.points_count;
            this.SegmentsCount = data.result.segments_count;
            this.VectorsSize = data.result.config.@params.vectors.size;
            this.Distance = data.result.config.@params.vectors.distance;
        }
        catch (Exception e)
        {
            ConsoleLogger<FetchCollectionResponse>.Log.Error(
                e, "JSON parse error: {0}", (string)System.Text.Json.JsonSerializer.Serialize(data));
            throw;
        }
    }

    #endregion
}
