// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Mapper between a Qdrant record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class QdrantVectorStoreRecordMapper<TRecord>(VectorStoreRecordModel model, bool hasNamedVectors)
    : IVectorStoreRecordMapper<TRecord, PointStruct>
{
    /// <inheritdoc />
    public PointStruct MapFromDataToStorageModel(TRecord dataModel)
    {
        var keyProperty = model.KeyProperty;

        var pointId = keyProperty.Type switch
        {
            var t when t == typeof(ulong) => new PointId
            {
                Num = (ulong?)keyProperty.GetValueAsObject(dataModel!) ?? throw new VectorStoreRecordMappingException($"Missing key property '{keyProperty.ModelName}' on provided record of type '{typeof(TRecord).Name}'.")
            },

            var t when t == typeof(Guid) => new PointId
            {
                Uuid = ((Guid?)keyProperty.GetValueAsObject(dataModel!))?.ToString("D") ?? throw new VectorStoreRecordMappingException($"Missing key property '{keyProperty.ModelName}' on provided record of type '{typeof(TRecord).Name}'.")
            },
            _ => throw new VectorStoreRecordMappingException($"Unsupported key type '{keyProperty.Type.Name}' for key property '{keyProperty.ModelName}' on provided record of type '{typeof(TRecord).Name}'.")
        };

        // Create point.
        var pointStruct = new PointStruct
        {
            Id = pointId,
            Vectors = new Vectors(),
            Payload = { },
        };

        // Add point payload.
        foreach (var property in model.DataProperties)
        {
            var propertyValue = property.GetValueAsObject(dataModel!);
            pointStruct.Payload.Add(property.StorageName, QdrantVectorStoreRecordFieldMapping.ConvertToGrpcFieldValue(propertyValue));
        }

        // Add vectors.
        if (hasNamedVectors)
        {
            var namedVectors = new NamedVectors();
            foreach (var property in model.VectorProperties)
            {
                var propertyValue = property.GetValueAsObject(dataModel!);
                if (propertyValue is not null)
                {
                    var castPropertyValue = (ReadOnlyMemory<float>)propertyValue;
                    namedVectors.Vectors.Add(property.StorageName, castPropertyValue.ToArray());
                }
            }

            pointStruct.Vectors.Vectors_ = namedVectors;
        }
        else
        {
            // We already verified in the constructor via FindProperties that there is exactly one vector property when not using named vectors.
            var property = model.VectorProperty;
            if (property.GetValueAsObject(dataModel!) is ReadOnlyMemory<float> floatROM)
            {
                pointStruct.Vectors.Vector = floatROM.ToArray();
            }
            else
            {
                throw new VectorStoreRecordMappingException($"Vector property '{property.ModelName}' on provided record of type '{typeof(TRecord).Name}' may not be null when not using named vectors.");
            }
        }

        return pointStruct;
    }

    /// <inheritdoc />
    public TRecord MapFromStorageToDataModel(PointStruct storageModel, StorageToDataModelMapperOptions options)
    {
        var outputRecord = model.CreateRecord<TRecord>()!;

        // TODO: Set the following generically to avoid boxing
        model.KeyProperty.SetValueAsObject(outputRecord, storageModel.Id switch
        {
            { HasNum: true } => storageModel.Id.Num,
            { HasUuid: true } => Guid.Parse(storageModel.Id.Uuid),
            _ => throw new UnreachableException()
        });

        // Set each vector property if embeddings are included in the point.
        if (options?.IncludeVectors is true)
        {
            if (hasNamedVectors)
            {
                var storageVectors = storageModel.Vectors.Vectors_.Vectors;

                foreach (var vectorProperty in model.VectorProperties)
                {
                    vectorProperty.SetValueAsObject(
                        outputRecord,
                        new ReadOnlyMemory<float>(storageVectors[vectorProperty.StorageName].Data.ToArray()));
                }
            }
            else
            {
                model.VectorProperty.SetValueAsObject(
                    outputRecord,
                    new ReadOnlyMemory<float>(storageModel.Vectors.Vector.Data.ToArray()));
            }
        }

        var payload = storageModel.Payload;

        foreach (var dataProperty in model.DataProperties)
        {
            if (payload.TryGetValue(dataProperty.StorageName, out var fieldValue))
            {
                dataProperty.SetValueAsObject(
                    outputRecord,
                    QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValueToNativeType(fieldValue, dataProperty.Type));
            }
        }

        return outputRecord;
    }
}
