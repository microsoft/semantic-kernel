// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal sealed class RecordMapper<TRecord>(VectorStoreRecordModel model)
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

            // We restrict the vector properties to ReadOnlyMemory<float> in model validation
            map[property.StorageName] = generatedEmbeddings?[i] is IReadOnlyList<Embedding> e
                ? e[recordIndex] switch
                {
                    Embedding<float> fe => fe.Vector,
                    _ => throw new UnreachableException()
                }
                : (ReadOnlyMemory<float>)property.GetValueAsObject(dataModel!)!;
        }

        return map;
    }

    public TRecord MapFromStorageToDataModel(IDictionary<string, object?> storageModel, StorageToDataModelMapperOptions options)
    {
        var record = model.CreateRecord<TRecord>()!;

        SetValue(storageModel, record, model.KeyProperty, storageModel[model.KeyProperty.StorageName]);

        foreach (var property in model.DataProperties)
        {
            SetValue(storageModel, record, property, storageModel[property.StorageName]);
        }

        if (options.IncludeVectors)
        {
            foreach (var property in model.VectorProperties)
            {
                var value = storageModel[property.StorageName];

                if (value is not null)
                {
                    if (value is ReadOnlyMemory<float> floats)
                    {
                        SetValue(storageModel, record, property, floats);
                    }
                    else
                    {
                        // When deserializing a string to a ReadOnlyMemory<float> fails in SqlDataReaderDictionary,
                        // we store the raw value so the user can handle the error in a custom mapper.
                        throw new VectorStoreRecordMappingException($"Failed to deserialize vector property '{property.ModelName}', it contained value '{value}'.");
                    }
                }
            }
        }

        return record;

        static void SetValue(IDictionary<string, object?> storageModel, object record, VectorStoreRecordPropertyModel property, object? value)
        {
            try
            {
                property.SetValueAsObject(record, value);
            }
            catch (Exception ex)
            {
                throw new VectorStoreRecordMappingException($"Failed to set value '{value}' on property '{property.ModelName}' of type '{property.Type.Name}'.", ex);
            }
        }
    }
}
