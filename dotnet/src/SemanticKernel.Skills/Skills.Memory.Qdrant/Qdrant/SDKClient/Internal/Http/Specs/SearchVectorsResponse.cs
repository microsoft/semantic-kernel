// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Http.Specs;

internal class SearchVectorsResponse
{
    internal class VectorFound
    {
        internal string QdrantId { get; set; } = string.Empty;
        internal float[] Vector { get; set; } = Array.Empty<float>();
        internal int Version { get; set; }
        internal double? Score { get; set; }
        internal string ExternalId { get; set; } = string.Empty;
        internal Dictionary<string, object> ExternalPayload { get; set; } = new();
        internal List<string> ExternalTags { get; set; } = new();

        internal VectorFound()
        {
            this.Version = 0;
            this.ExternalTags = new List<string>();
        }
    }

    internal string Status { get; set; }
    internal List<VectorFound> Vectors { get; set; }

    internal SearchVectorsResponse(string json) : this()
    {
        // TODO: Replace with a System.Text.Json implementation
        dynamic value = JObject.Parse(json);
        FromDynamic(value);
    }

    #region private ================================================================================

    private SearchVectorsResponse()
    {
        this.Status = "";
        this.Vectors = new List<VectorFound>();
    }

    private void FromDynamic(dynamic data)
    {
        if (data == null)
        {
            throw new ArgumentNullException(nameof(data), "Cannot extract search response object from NULL");
        }

        this.Status = data.status;
        if (data.result != null)
        {
            foreach (var point in data.result)
            {
                var vector = new VectorFound
                {
                    QdrantId = point.id,
                    Version = (int)point.version,
                    Score = point.score,
                };

                // The payload is optional
                if (point.payload != null)
                {
                    vector.ExternalId = PointPayloadDataMapper.GetExternalIdFromQdrantPayload(point.payload);
                    vector.ExternalTags = PointPayloadDataMapper.GetTagsFromQdrantPayload(point.payload);
                    vector.ExternalPayload = PointPayloadDataMapper.GetUserPayloadFromQdrantPayload(point.payload);
                }

                // The vector data is optional
                if (point.vector != null)
                {
                    vector.Vector = point.vector.ToObject<float[]>();
                }

                this.Vectors.Add(vector);
            }
        }
    }

    #endregion
}
