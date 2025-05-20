// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal sealed class SqlServerMapper<TRecord>(CollectionModel model)
{
    public IDictionary<string, object?> MapFromDataToStorageModel(TRecord dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        Dictionary<string, object?> map = new(StringComparer.Ordinal);

        map[model.KeyProperty.StorageName] = model.KeyProperty.GetValueAsObject(dataModel!);

        foreach (var property in model.DataProperties)
        {
            map[property.StorageName] = property.GetValueAsObject(dataModel!);
        }

        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            var vector = generatedEmbeddings?[i] is IReadOnlyList<Embedding> ge
                ? ge[recordIndex]
                : property.GetValueAsObject(dataModel!)!;

            map[property.StorageName] = vector switch
            {
                ReadOnlyMemory<float> m => m,
                Embedding<float> e => e.Vector,
                float[] a => a,

                _ => throw new UnreachableException()
            };
        }

        return map;
    }

    public TRecord MapFromStorageToDataModel(IDictionary<string, object?> storageModel, bool includeVectors)
    {
        var record = model.CreateRecord<TRecord>()!;

        SetValue(storageModel, record, model.KeyProperty, storageModel[model.KeyProperty.StorageName]);

        foreach (var property in model.DataProperties)
        {
            SetValue(storageModel, record, property, storageModel[property.StorageName]);
        }

        if (includeVectors)
        {
            foreach (var property in model.VectorProperties)
            {
                var value = storageModel[property.StorageName];

                if (value is not null)
                {
                    if (value is ReadOnlyMemory<float> floats)
                    {
                        property.SetValueAsObject(record, property.Type switch
                        {
                            var t when t == typeof(ReadOnlyMemory<float>) => value,
                            var t when t == typeof(Embedding<float>) => new Embedding<float>(floats),
                            var t when t == typeof(float[])
                                => MemoryMarshal.TryGetArray(floats, out ArraySegment<float> segment) && segment.Count == segment.Array!.Length
                                    ? segment.Array
                                    : floats.ToArray(),

                            _ => throw new UnreachableException()
                        });
                    }
                    else
                    {
                        // When deserializing a string to a ReadOnlyMemory<float> fails in SqlDataReaderDictionary,
                        // we store the raw value so the user can handle the error in a custom mapper.
                        throw new InvalidOperationException($"Failed to deserialize vector property '{property.ModelName}', it contained value '{value}'.");
                    }
                }
            }
        }

        return record;

        static void SetValue(IDictionary<string, object?> storageModel, object record, PropertyModel property, object? value)
        {
            try
            {
                property.SetValueAsObject(record, value);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Failed to set value '{value}' on property '{property.ModelName}' of type '{property.Type.Name}'.", ex);
            }
        }
    }
}
