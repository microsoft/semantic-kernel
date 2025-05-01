// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Class for mapping between a dictionary and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class SqliteVectorStoreRecordMapper<TRecord>(VectorStoreRecordModel model)
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
            var vector = generatedEmbeddings?[i] is IReadOnlyList<Embedding> e ? ((Embedding<float>)e[recordIndex]).Vector : property.GetValueAsObject(dataModel!);

            properties.Add(
                property.StorageName,
                vector switch
                {
                    ReadOnlyMemory<float> floats => SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(floats),
                    null => null,
                    _ => throw new InvalidOperationException($"Retrieved value for vector property '{property.StorageName}' which is not a ReadOnlyMemory<float> ('{vector?.GetType().Name}').")
                });
        }

        return properties;
    }

    public TRecord MapFromStorageToDataModel(Dictionary<string, object?> storageModel, StorageToDataModelMapperOptions options)
    {
        var record = model.CreateRecord<TRecord>()!;

        var keyPropertyValue = Convert.ChangeType(storageModel[model.KeyProperty.StorageName], model.KeyProperty.Type);
        model.KeyProperty.SetValueAsObject(record, keyPropertyValue);

        foreach (var property in model.DataProperties)
        {
            property.SetValueAsObject(record, storageModel[property.StorageName]);
        }

        if (options.IncludeVectors)
        {
            foreach (var property in model.VectorProperties)
            {
                if (storageModel[property.StorageName] is not byte[] vectorBytes)
                {
                    throw new InvalidOperationException($"Retrieved value for vector property '{property.StorageName}' which is not a byte array ('{storageModel[property.StorageName]?.GetType().Name}').");
                }

                property.SetValueAsObject(record, SqliteVectorStoreRecordPropertyMapping.MapVectorForDataModel(vectorBytes));
            }
        }

        return record;
    }
}
