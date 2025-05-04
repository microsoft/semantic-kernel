﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Mapper between a Pinecone record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class PineconeMapper<TRecord>(Extensions.VectorData.ConnectorSupport.CollectionModel model)
{
    /// <inheritdoc />
    public Vector MapFromDataToStorageModel(TRecord dataModel, Embedding<float>? generatedEmbedding)
    {
        var keyObject = model.KeyProperty.GetValueAsObject(dataModel!);
        if (keyObject is null)
        {
            throw new InvalidOperationException($"Key property '{model.KeyProperty.ModelName}' on provided record of type '{typeof(TRecord).Name}' may not be null.");
        }

        var metadata = new Metadata();
        foreach (var property in model.DataProperties)
        {
            if (property.GetValueAsObject(dataModel!) is { } value)
            {
                metadata[property.StorageName] = PineconeFieldMapping.ConvertToMetadataValue(value);
            }
        }

        var values = (generatedEmbedding?.Vector ?? model.VectorProperty!.GetValueAsObject(dataModel!)) switch
        {
            ReadOnlyMemory<float> floats => floats,
            null => throw new InvalidOperationException($"Vector property '{model.VectorProperty.ModelName}' on provided record of type '{typeof(TRecord).Name}' may not be null."),
            _ => throw new InvalidOperationException($"Unsupported vector type '{model.VectorProperty.Type.Name}' for vector property '{model.VectorProperty.ModelName}' on provided record of type '{typeof(TRecord).Name}'.")
        };

        // TODO: what about sparse values?
        var result = new Vector
        {
            Id = (string)keyObject,
            Values = values,
            Metadata = metadata,
            SparseValues = null
        };

        return result;
    }

    /// <inheritdoc />
    public TRecord MapFromStorageToDataModel(Vector storageModel, bool includeVectors)
    {
        var outputRecord = model.CreateRecord<TRecord>()!;

        model.KeyProperty.SetValueAsObject(outputRecord, storageModel.Id);

        if (includeVectors is true)
        {
            model.VectorProperty.SetValueAsObject(
                outputRecord,
                storageModel.Values);
        }

        if (storageModel.Metadata != null)
        {
            foreach (var property in model.DataProperties)
            {
                property.SetValueAsObject(
                    outputRecord,
                    storageModel.Metadata.TryGetValue(property.StorageName, out var metadataValue) && metadataValue is not null
                        ? PineconeFieldMapping.ConvertFromMetadataValueToNativeType(metadataValue, property.Type)
                        : null);
            }
        }

        return outputRecord;
    }
}
