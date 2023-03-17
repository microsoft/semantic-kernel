// Copyright (c) Microsoft. All rights reserved.

using System;
using Newtonsoft.Json.Linq;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal class FetchCollectionResponse
{
    internal FetchCollectionResponse(string json)
    {
        // TODO: Replace with a System.Text.Json implementation
        dynamic value = JObject.Parse(json);
        FromDynamic(value);
    }

    internal CollectionData CollectionInfo 
    { 
        get => _collectionData; 
        set => _collectionData = value ?? throw new ArgumentNullException(nameof(value));; 
    }

    #region private ================================================================================
    private CollectionData _collectionData;

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
