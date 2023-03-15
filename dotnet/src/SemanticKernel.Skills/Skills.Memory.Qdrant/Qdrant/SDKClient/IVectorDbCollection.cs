// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient;

[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix", Justification = "It is a collection")]
public interface IVectorDbCollection
{
    string Name { get; }

    IAsyncEnumerable<DataEntry<VectorRecordData<float>>> GetAllVectorsAsync();
    Task<DataEntry<VectorRecordData<float>>?> GetVectorAsync(string id);
    Task UpsertVectorAsync(DataEntry<VectorRecordData<float>> record);
    Task DeleteVectorAsync(string id);
    IAsyncEnumerable<KeyValuePair<DataEntry<VectorRecordData<float>>, double>> FindClosestAsync(float[] target, int top = 1, string[]? requiredTags = null);
}

public static class VectorDbCollectionExtensions
{
    public static Task UpsertVectorAsync(this IVectorDbCollection collection, string id, float[] data, IEnumerable<string>? tags = null,
        Dictionary<string, object>? payload = null)
    {
        IVectorDbCollection vectorColl = collection;
        return collection.UpsertVectorAsync(
            new DataEntry<VectorRecordData<float>>(key: id,
                value: new VectorRecordData<float>(
                    new Embedding<float>(data),
                    payload ?? new(),
                    tags?.ToList() ?? new List<string>(0))));
    }

    public static Task DeleteVectorAsync(this IVectorDbCollection collection, DataEntry<VectorRecordData<float>> record)
    {
        return collection.DeleteVectorAsync(record.Key);
    }

    public static IAsyncEnumerable<KeyValuePair<DataEntry<VectorRecordData<float>>, double>> FindClosestAsync(this IVectorDbCollection collection,
        DataEntry<VectorRecordData<float>> record, int top = 1, string[]? requiredTags = null)
    {
        return collection.FindClosestAsync(record.Value!.Embedding.Vector.ToArray(), top, requiredTags);
    }
}
