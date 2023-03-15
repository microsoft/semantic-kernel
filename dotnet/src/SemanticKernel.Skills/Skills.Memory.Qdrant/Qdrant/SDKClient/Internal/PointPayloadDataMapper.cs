// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Memory.Storage;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal;

/// <summary>
/// Mapping of our content ID and Qdrant point IDs.
/// Qdrant is picky about its vectors IDs, which must be either a GUID or a number.
/// We use only GUIDs, however, we also dereference the "content ID" (e.g. email ID) from the vector ID.
/// Qdrant vector ID is automagically managed by the code here, and we store the content ID
/// inside Qdrant vectors' payload, as "externalId".
/// Qdrant allows to query by payload, so if we ever need we can, though we should avoid using
/// Qdrant as a data storage, running only vector queries.
/// Note: Qdrant uses the term "point" for vectors, but not always...
/// </summary>
internal static class PointPayloadDataMapper
{
    internal const string VECTOR_ID_FIELD = "externalId";
    internal const string VECTOR_TAGS_FIELD = "externalTags";

    // This fields holds the Vector ID chosen by the user, which is not the internal Qdrant vector/point ID
    internal static string GetExternalIdFromQdrantPayload(dynamic qdrantPayload)
    {
        return qdrantPayload.externalId;
    }

    // We store custom optional tags inside the vector payload, to enable search by tag
    internal static List<string> GetTagsFromQdrantPayload(dynamic qdrantPayload)
    {
        var result = new List<string>();
        if (qdrantPayload.externalTags == null) { return result; }

        foreach (string tag in qdrantPayload.externalTags)
        {
            result.Add(tag);
        }

        return result;
    }

    // We store a custom dictionary/property bag inside the vector payload, to attach custom data such as document IDs.
    internal static Dictionary<string, object> GetUserPayloadFromQdrantPayload(dynamic qdrantPayload)
    {
        if (qdrantPayload.externalPayload == null)
        {
            return new Dictionary<string, object>();
        }

        return qdrantPayload.externalPayload.ToObject<Dictionary<string, object>>();
    }

    // Map our custom data into Qdrant point payload
    internal static object PreparePointPayload(DataEntry<VectorRecordData<float>> vector)
    {
        var tags = new List<string>();
        if (vector.Value.Tags != null)
        {
            tags = vector.Value.Tags;
        }

        return new
        {
            externalId = vector.Key,
            externalTags = tags,
            externalPayload = vector.Value.Payload
        };
    }
}
