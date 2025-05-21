// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

/// <summary>
/// Class for mapping between a dictionary and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class SqliteMapper<TRecord>(CollectionModel model)
{
    public Dictionary<string, object?> MapFromDataToStorageModel(TRecord dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        var properties = new Dictionary<string, object?>
        {
            { model.KeyProperty.StorageName, model.KeyProperty.GetValueAsObject(dataModel!) }
        };

        foreach (var property in model.DataProperties)
        {
            properties.Add(property.StorageName, property.GetValueAsObject(dataModel!));
        }

        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];
            var vector = generatedEmbeddings?[i] is IReadOnlyList<Embedding> ge ? ((Embedding<float>)ge[recordIndex]).Vector : property.GetValueAsObject(dataModel!);

            properties.Add(
                property.StorageName,
                vector switch
                {
                    ReadOnlyMemory<float> m => SqlitePropertyMapping.MapVectorForStorageModel(m),
                    Embedding<float> e => SqlitePropertyMapping.MapVectorForStorageModel(e.Vector),
                    float[] a => SqlitePropertyMapping.MapVectorForStorageModel(a),
                    null => null,

                    _ => throw new InvalidOperationException($"Retrieved value for vector property '{property.StorageName}' which is not a ReadOnlyMemory<float> ('{vector?.GetType().Name}').")
                });
        }

        return properties;
    }

    public TRecord MapFromStorageToDataModel(Dictionary<string, object?> storageModel, bool includeVectors)
    {
        var record = model.CreateRecord<TRecord>()!;

        var keyPropertyValue = Convert.ChangeType(storageModel[model.KeyProperty.StorageName], model.KeyProperty.Type);
        model.KeyProperty.SetValueAsObject(record, keyPropertyValue);

        foreach (var property in model.DataProperties)
        {
            property.SetValueAsObject(record, storageModel[property.StorageName]);
        }

        if (includeVectors)
        {
            foreach (var property in model.VectorProperties)
            {
                if (storageModel[property.StorageName] is not byte[] vectorBytes)
                {
                    throw new InvalidOperationException($"Retrieved value for vector property '{property.StorageName}' which is not a byte array ('{storageModel[property.StorageName]?.GetType().Name}').");
                }

                var memory = SqlitePropertyMapping.MapVectorForDataModel(vectorBytes);

                property.SetValueAsObject(
                    record,
                    (Nullable.GetUnderlyingType(property.Type) ?? property.Type) switch
                    {
                        var t when t == typeof(ReadOnlyMemory<float>) => memory,
                        var t when t == typeof(Embedding<float>) => new Embedding<float>(memory),
                        var t when t == typeof(float[])
                            => MemoryMarshal.TryGetArray(memory, out ArraySegment<float> segment) && segment.Count == segment.Array!.Length
                                ? segment.Array
                                : memory.ToArray(),

                        _ => throw new UnreachableException()
                    });
            }
        }

        return record;
    }
}
