// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Linq;
using Google.Protobuf.Collections;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Mapper between a Qdrant record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class QdrantVectorStoreRecordMapper<TRecord>(VectorStoreRecordModel model, bool hasNamedVectors)
{
    /// <inheritdoc />
    public PointStruct MapFromDataToStorageModel(TRecord dataModel, int recordIndex, GeneratedEmbeddings<Embedding<float>>?[]? generatedEmbeddings)
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

            for (var i = 0; i < model.VectorProperties.Count; i++)
            {
                var property = model.VectorProperties[i];

                namedVectors.Vectors.Add(
                    property.StorageName,
                    GetVector(
                        property,
                        generatedEmbeddings?[i] is GeneratedEmbeddings<Embedding<float>> e
                            ? e[recordIndex]
                            : property.GetValueAsObject(dataModel!)));
            }

            pointStruct.Vectors.Vectors_ = namedVectors;
        }
        else
        {
            // We already verified in the constructor via FindProperties that there is exactly one vector property when not using named vectors.
            Debug.Assert(
                generatedEmbeddings is null || generatedEmbeddings.Length == 1 && generatedEmbeddings[0] is not null,
                "There should be exactly one generated embedding when not using named vectors (single vector property).");
            pointStruct.Vectors.Vector = GetVector(
                model.VectorProperty,
                generatedEmbeddings is null
                    ? model.VectorProperty.GetValueAsObject(dataModel!)
                    : generatedEmbeddings[0]![recordIndex].Vector);
        }

        return pointStruct;

        Vector GetVector(VectorStoreRecordPropertyModel property, object? embedding)
            => embedding switch
            {
                ReadOnlyMemory<float> floatVector => floatVector.ToArray(),
                null => throw new VectorStoreRecordMappingException($"Vector property '{property.ModelName}' on provided record of type '{typeof(TRecord).Name}' may not be null when not using named vectors."),
                var unknownEmbedding => throw new VectorStoreRecordMappingException($"Vector property '{property.ModelName}' on provided record of type '{typeof(TRecord).Name}' has unsupported embedding type '{unknownEmbedding.GetType().Name}'.")
            };
    }

    /// <inheritdoc />
    public TRecord MapFromStorageToDataModel(PointId pointId, MapField<string, Value> payload, VectorsOutput vectorsOutput, StorageToDataModelMapperOptions options)
    {
        var outputRecord = model.CreateRecord<TRecord>()!;

        // TODO: Set the following generically to avoid boxing
        model.KeyProperty.SetValueAsObject(outputRecord, pointId switch
        {
            { HasNum: true } => pointId.Num,
            { HasUuid: true } => Guid.Parse(pointId.Uuid),
            _ => throw new UnreachableException()
        });

        // Set each vector property if embeddings are included in the point.
        if (options?.IncludeVectors is true)
        {
            if (hasNamedVectors)
            {
                var storageVectors = vectorsOutput.Vectors.Vectors;

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
                    new ReadOnlyMemory<float>(vectorsOutput.Vector.Data.ToArray()));
            }
        }

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
