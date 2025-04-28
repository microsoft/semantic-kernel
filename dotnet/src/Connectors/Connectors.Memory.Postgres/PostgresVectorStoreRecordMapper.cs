// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// A mapper class that handles the conversion between data models and storage models for Postgres vector store.
/// </summary>
/// <typeparam name="TRecord">The type of the data model record.</typeparam>
internal sealed class PostgresVectorStoreRecordMapper<TRecord>(VectorStoreRecordModel model)
    where TRecord : notnull
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
                PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(
                    generatedEmbeddings?[i] is IReadOnlyList<Embedding> e
                        ? e[recordIndex] switch
                        {
                            Embedding<float> fe => fe.Vector,
                            _ => throw new UnreachableException()
                        }
                        : (ReadOnlyMemory<float>?)property.GetValueAsObject(dataModel!)!));
        }

        return properties;
    }

    public TRecord MapFromStorageToDataModel(Dictionary<string, object?> storageModel, StorageToDataModelMapperOptions options)
    {
        var record = model.CreateRecord<TRecord>()!;

        var keyProperty = model.KeyProperty;
        var keyPropertyValue = Convert.ChangeType(storageModel[keyProperty.StorageName], keyProperty.Type);
        keyProperty.SetValueAsObject(record, keyPropertyValue);

        foreach (var dataProperty in model.DataProperties)
        {
            dataProperty.SetValueAsObject(record, storageModel[dataProperty.StorageName]);
        }

        if (options.IncludeVectors)
        {
            foreach (var vectorProperty in model.VectorProperties)
            {
                switch (storageModel[vectorProperty.StorageName])
                {
                    case Pgvector.Vector pgVector:
                        vectorProperty.SetValueAsObject(record, pgVector.Memory);
                        continue;

                    // TODO: Implement support for Half, binary, sparse embeddings (#11083)

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
