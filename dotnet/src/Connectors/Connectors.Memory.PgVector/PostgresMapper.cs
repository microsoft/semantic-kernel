// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// A mapper class that handles the conversion between data models and storage models for Postgres vector store.
/// </summary>
/// <typeparam name="TRecord">The type of the data model record.</typeparam>
internal sealed class PostgresMapper<TRecord>(CollectionModel model)
    where TRecord : class
{
    public Dictionary<string, object?> MapFromDataToStorageModel(TRecord dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        var keyProperty = model.KeyProperty;

        var properties = new Dictionary<string, object?>
        {
            { keyProperty.StorageName, keyProperty.GetValueAsObject(dataModel) }
        };

        foreach (var property in model.DataProperties)
        {
            properties.Add(property.StorageName, property.GetValueAsObject(dataModel));
        }

        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            properties.Add(
                property.StorageName,
                PostgresPropertyMapping.MapVectorForStorageModel(
                    generatedEmbeddings?[i] is IReadOnlyList<Embedding> e
                        ? e[recordIndex]
                        : property.GetValueAsObject(dataModel!)));
        }

        return properties;
    }

    public TRecord MapFromStorageToDataModel(Dictionary<string, object?> storageModel, bool includeVectors)
    {
        var record = model.CreateRecord<TRecord>()!;

        var keyProperty = model.KeyProperty;
        var keyPropertyValue = Convert.ChangeType(storageModel[keyProperty.StorageName], keyProperty.Type);
        keyProperty.SetValueAsObject(record, keyPropertyValue);

        foreach (var dataProperty in model.DataProperties)
        {
            dataProperty.SetValueAsObject(record, storageModel[dataProperty.StorageName]);
        }

        if (includeVectors)
        {
            foreach (var vectorProperty in model.VectorProperties)
            {
                switch (storageModel[vectorProperty.StorageName])
                {
                    case Pgvector.Vector { Memory: ReadOnlyMemory<float> memory }:
                    {
                        vectorProperty.SetValueAsObject(record, (Nullable.GetUnderlyingType(vectorProperty.Type) ?? vectorProperty.Type) switch
                        {
                            var t when t == typeof(ReadOnlyMemory<float>) => memory,
                            var t when t == typeof(Embedding<float>) => new Embedding<float>(memory),
                            var t when t == typeof(float[])
                                => MemoryMarshal.TryGetArray(memory, out ArraySegment<float> segment) && segment.Count == segment.Array!.Length
                                    ? segment.Array
                                    : memory.ToArray(),

                            _ => throw new UnreachableException()
                        });
                        continue;
                    }

#if NET8_0_OR_GREATER
                    case Pgvector.HalfVector { Memory: ReadOnlyMemory<Half> memory }:
                    {
                        vectorProperty.SetValueAsObject(record, (Nullable.GetUnderlyingType(vectorProperty.Type) ?? vectorProperty.Type) switch
                        {
                            var t when t == typeof(ReadOnlyMemory<Half>) => memory,
                            var t when t == typeof(Embedding<Half>) => new Embedding<Half>(memory),
                            var t when t == typeof(Half[])
                                => MemoryMarshal.TryGetArray(memory, out ArraySegment<Half> segment) && segment.Count == segment.Array!.Length
                                    ? segment.Array
                                    : memory.ToArray(),

                            _ => throw new UnreachableException()
                        });
                        continue;
                    }
#endif

                    case BitArray bitArray:
                        vectorProperty.SetValueAsObject(record, bitArray);
                        continue;

                    case Pgvector.SparseVector pgSparseVector:
                        vectorProperty.SetValueAsObject(record, pgSparseVector);
                        continue;

                    // TODO: We currently allow round-tripping null for the vector property; this is not supported for most (?) dedicated databases; think about it.
                    case null:
                        vectorProperty.SetValueAsObject(record, null);
                        continue;

                    case var value:
                        throw new InvalidOperationException($"Embedding vector read back from PostgreSQL is of type '{value.GetType().Name}' instead of the expected Pgvector.Vector type for property '{vectorProperty.ModelName}'.");
                }
            }
        }

        return record;
    }
}
