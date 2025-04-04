// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Mapper between a Pinecone record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
internal sealed class PineconeVectorStoreRecordMapper<TRecord>(VectorStoreRecordModel model) : IVectorStoreRecordMapper<TRecord, Vector>
#pragma warning restore CS0618
{
    /// <inheritdoc />
    public Vector MapFromDataToStorageModel(TRecord dataModel)
    {
        var keyObject = model.KeyProperty.GetValueAsObject(dataModel!);
        if (keyObject is null)
        {
            throw new VectorStoreRecordMappingException($"Key property '{model.KeyProperty.ModelName}' on provided record of type '{typeof(TRecord).Name}' may not be null.");
        }

        var metadata = new Metadata();
        foreach (var property in model.DataProperties)
        {
            if (property.GetValueAsObject(dataModel!) is { } value)
            {
                metadata[property.StorageName] = PineconeVectorStoreRecordFieldMapping.ConvertToMetadataValue(value);
            }
        }

        var valuesObject = model.VectorProperty!.GetValueAsObject(dataModel!);
        if (valuesObject is not ReadOnlyMemory<float> values)
        {
            throw new VectorStoreRecordMappingException($"Vector property '{model.VectorProperty.ModelName}' on provided record of type '{typeof(TRecord).Name}' may not be null.");
        }

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
    public TRecord MapFromStorageToDataModel(Vector storageModel, StorageToDataModelMapperOptions options)
    {
        var outputRecord = model.CreateRecord<TRecord>()!;

        model.KeyProperty.SetValueAsObject(outputRecord, storageModel.Id);

        if (options?.IncludeVectors is true)
        {
            model.VectorProperty.SetValueAsObject(
                outputRecord,
                storageModel.Values);
        }

        if (storageModel.Metadata != null)
        {
            foreach (var property in model.DataProperties)
            {
                if (storageModel.Metadata.TryGetValue(property.StorageName, out var metadataValue))
                {
                    property.SetValueAsObject(
                        outputRecord,
                        metadataValue is null ? null : PineconeVectorStoreRecordFieldMapping.ConvertFromMetadataValueToNativeType(metadataValue, property.Type));
                }
            }
        }

        return outputRecord;
    }
}
