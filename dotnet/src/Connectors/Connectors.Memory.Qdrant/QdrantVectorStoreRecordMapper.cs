// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Mapper between a Qdrant record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class QdrantVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, PointStruct>
{
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</summary>
    private readonly bool _hasNamedVectors;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreRecordMapper{TDataModel}"/> class.
    /// </summary>
    /// <param name="propertyReader">A helper to access property information for the current data model and record definition.</param>
    /// <param name="hasNamedVectors">A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</param>
    public QdrantVectorStoreRecordMapper(
        VectorStoreRecordPropertyReader propertyReader,
        bool hasNamedVectors)
    {
        Verify.NotNull(propertyReader);

        // Validate property types.
        propertyReader.VerifyHasParameterlessConstructor();
        propertyReader.VerifyDataProperties(QdrantVectorStoreRecordFieldMapping.s_supportedDataTypes, supportEnumerable: true);
        propertyReader.VerifyVectorProperties(QdrantVectorStoreRecordFieldMapping.s_supportedVectorTypes);

        // Assign.
        this._propertyReader = propertyReader;
        this._hasNamedVectors = hasNamedVectors;
    }

    /// <inheritdoc />
    public PointStruct MapFromDataToStorageModel(TRecord dataModel)
    {
        PointId pointId;
        var keyPropertyInfo = this._propertyReader.KeyPropertyInfo;
        if (keyPropertyInfo.PropertyType == typeof(ulong))
        {
            var key = keyPropertyInfo.GetValue(dataModel) as ulong? ?? throw new VectorStoreRecordMappingException($"Missing key property {keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName}.");
            pointId = new PointId { Num = key };
        }
        else if (keyPropertyInfo.PropertyType == typeof(Guid))
        {
            var key = keyPropertyInfo.GetValue(dataModel) as Guid? ?? throw new VectorStoreRecordMappingException($"Missing key property {keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName}.");
            pointId = new PointId { Uuid = key.ToString("D") };
        }
        else
        {
            throw new VectorStoreRecordMappingException($"Unsupported key type {keyPropertyInfo.PropertyType.FullName} for key property {keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName}.");
        }

        // Create point.
        var pointStruct = new PointStruct
        {
            Id = pointId,
            Vectors = new Vectors(),
            Payload = { },
        };

        // Add point payload.
        foreach (var dataPropertyInfo in this._propertyReader.DataPropertiesInfo)
        {
            var propertyName = this._propertyReader.GetStoragePropertyName(dataPropertyInfo.Name);
            var propertyValue = dataPropertyInfo.GetValue(dataModel);
            pointStruct.Payload.Add(propertyName, QdrantVectorStoreRecordFieldMapping.ConvertToGrpcFieldValue(propertyValue));
        }

        // Add vectors.
        if (this._hasNamedVectors)
        {
            var namedVectors = new NamedVectors();
            foreach (var vectorPropertyInfo in this._propertyReader.VectorPropertiesInfo)
            {
                var propertyName = this._propertyReader.GetStoragePropertyName(vectorPropertyInfo.Name);
                var propertyValue = vectorPropertyInfo.GetValue(dataModel);
                if (propertyValue is not null)
                {
                    var castPropertyValue = (ReadOnlyMemory<float>)propertyValue;
                    namedVectors.Vectors.Add(propertyName, castPropertyValue.ToArray());
                }
            }

            pointStruct.Vectors.Vectors_ = namedVectors;
        }
        else
        {
            // We already verified in the constructor via FindProperties that there is exactly one vector property when not using named vectors.
            var vectorPropertyInfo = this._propertyReader.FirstVectorPropertyInfo!;
            if (vectorPropertyInfo.GetValue(dataModel) is ReadOnlyMemory<float> floatROM)
            {
                pointStruct.Vectors.Vector = floatROM.ToArray();
            }
            else
            {
                throw new VectorStoreRecordMappingException($"Vector property {vectorPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName} may not be null when not using named vectors.");
            }
        }

        return pointStruct;
    }

    /// <inheritdoc />
    public TRecord MapFromStorageToDataModel(PointStruct storageModel, StorageToDataModelMapperOptions options)
    {
        // Get the key property name and value.
        var keyPropertyValue = storageModel.Id.HasNum ? storageModel.Id.Num as object : new Guid(storageModel.Id.Uuid) as object;

        // Construct the output record.
        var outputRecord = (TRecord)this._propertyReader.ParameterLessConstructorInfo.Invoke(null);

        // Set Key
        this._propertyReader.KeyPropertyInfo.SetValue(outputRecord, keyPropertyValue);

        // Set each vector property if embeddings are included in the point.
        if (options?.IncludeVectors is true)
        {
            if (this._hasNamedVectors)
            {
                VectorStoreRecordMapping.SetValuesOnProperties(
                    outputRecord,
                    this._propertyReader.VectorPropertiesInfo,
                    this._propertyReader.StoragePropertyNamesMap,
                    storageModel.Vectors.Vectors_.Vectors,
                    (Vector vector, Type targetType) => new ReadOnlyMemory<float>(vector.Data.ToArray()));
            }
            else
            {
                this._propertyReader.FirstVectorPropertyInfo!.SetValue(
                    outputRecord,
                    new ReadOnlyMemory<float>(storageModel.Vectors.Vector.Data.ToArray()));
            }
        }

        // Set each data property.
        VectorStoreRecordMapping.SetValuesOnProperties(
            outputRecord,
            this._propertyReader.DataPropertiesInfo,
            this._propertyReader.StoragePropertyNamesMap,
            storageModel.Payload,
            QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValueToNativeType);

        return outputRecord;
    }
}
