// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Qdrant.
/// </summary>
internal class QdrantGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<ulong>, PointStruct>, IVectorStoreRecordMapper<VectorStoreGenericDataModel<Guid>, PointStruct>
{
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</summary>
    private readonly bool _hasNamedVectors;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantGenericDataModelMapper"/> class.
    /// </summary>
    /// <param name="propertyReader">A helper to access property information for the current data model and record definition.</param>
    /// <param name="hasNamedVectors">A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</param>
    public QdrantGenericDataModelMapper(
        VectorStoreRecordPropertyReader propertyReader,
        bool hasNamedVectors)
    {
        Verify.NotNull(propertyReader);

        // Validate property types.
        propertyReader.VerifyDataProperties(QdrantVectorStoreRecordFieldMapping.s_supportedDataTypes, supportEnumerable: true);
        propertyReader.VerifyVectorProperties(QdrantVectorStoreRecordFieldMapping.s_supportedVectorTypes);

        // Assign.
        this._propertyReader = propertyReader;
        this._hasNamedVectors = hasNamedVectors;
    }

    /// <inheritdoc />
    public PointStruct MapFromDataToStorageModel(VectorStoreGenericDataModel<ulong> dataModel)
    {
        // Create point.
        var pointStruct = new PointStruct
        {
            Id = new PointId { Num = dataModel.Key },
            Vectors = new Vectors(),
            Payload = { },
        };

        // Loop through all properties and map each from the data model to the storage model.
        MapProperties(
            this._propertyReader.Properties,
            dataModel.Data,
            dataModel.Vectors,
            pointStruct,
            this._hasNamedVectors);

        return pointStruct;
    }

    /// <inheritdoc />
    public VectorStoreGenericDataModel<ulong> MapFromStorageToDataModel(PointStruct storageModel, StorageToDataModelMapperOptions options)
    {
        var dataModel = new VectorStoreGenericDataModel<ulong>(storageModel.Id.Num);
        MapProperties(this._propertyReader.Properties, storageModel, dataModel.Data, dataModel.Vectors, this._hasNamedVectors);
        return dataModel;
    }

    /// <inheritdoc />
    PointStruct IVectorStoreRecordMapper<VectorStoreGenericDataModel<Guid>, PointStruct>.MapFromDataToStorageModel(VectorStoreGenericDataModel<Guid> dataModel)
    {
        // Create point.
        var pointStruct = new PointStruct
        {
            Id = new PointId { Uuid = dataModel.Key.ToString("D") },
            Vectors = new Vectors(),
            Payload = { },
        };

        // Loop through all properties and map each from the data model to the storage model.
        MapProperties(
            this._propertyReader.Properties,
            dataModel.Data,
            dataModel.Vectors,
            pointStruct,
            this._hasNamedVectors);

        return pointStruct;
    }

    /// <inheritdoc />
    VectorStoreGenericDataModel<Guid> IVectorStoreRecordMapper<VectorStoreGenericDataModel<Guid>, PointStruct>.MapFromStorageToDataModel(PointStruct storageModel, StorageToDataModelMapperOptions options)
    {
        var dataModel = new VectorStoreGenericDataModel<Guid>(new Guid(storageModel.Id.Uuid));
        MapProperties(this._propertyReader.Properties, storageModel, dataModel.Data, dataModel.Vectors, this._hasNamedVectors);
        return dataModel;
    }

    /// <summary>
    /// Map the payload and vector properties from the data model to the qdrant storage model.
    /// </summary>
    /// <param name="properties">The list of properties to map.</param>
    /// <param name="dataProperties">The payload properties on the data model.</param>
    /// <param name="vectorProperties">The vector properties on the data model.</param>
    /// <param name="pointStruct">The storage model to map to.</param>
    /// <param name="hasNamedVectors">A value indicating whether qdrant is using named vectors for this collection.</param>
    /// <exception cref="VectorStoreRecordMappingException">Thrown if a vector on the data model is not a supported type.</exception>
    private static void MapProperties(IEnumerable<VectorStoreRecordProperty> properties, Dictionary<string, object?> dataProperties, Dictionary<string, object?> vectorProperties, PointStruct pointStruct, bool hasNamedVectors)
    {
        if (hasNamedVectors)
        {
            pointStruct.Vectors.Vectors_ = new NamedVectors();
        }

        foreach (var property in properties)
        {
            if (property is VectorStoreRecordDataProperty dataProperty)
            {
                var storagePropertyName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;

                // Just skip this property if it's not in the data model.
                if (!dataProperties.TryGetValue(dataProperty.DataModelPropertyName, out var propertyValue))
                {
                    continue;
                }

                // Map.
                pointStruct.Payload.Add(storagePropertyName, QdrantVectorStoreRecordFieldMapping.ConvertToGrpcFieldValue(propertyValue));
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                var storagePropertyName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;

                // Just skip this property if it's not in the data model.
                if (!vectorProperties.TryGetValue(vectorProperty.DataModelPropertyName, out var vector))
                {
                    continue;
                }

                // Validate.
                if (vector is not ReadOnlyMemory<float> floatROM)
                {
                    throw new VectorStoreRecordMappingException($"Vector property '{vectorProperty.DataModelPropertyName}' on provided record of type {nameof(VectorStoreGenericDataModel<ulong>)} must be of type ReadOnlyMemory<float> and not null.");
                }

                // Map.
                if (hasNamedVectors)
                {
                    pointStruct.Vectors.Vectors_.Vectors.Add(storagePropertyName, floatROM.ToArray());
                }
                else
                {
                    pointStruct.Vectors.Vector = floatROM.ToArray();
                }
            }
        }
    }

    /// <summary>
    /// Map the payload and vector properties from the qdrant storage model to the data model.
    /// </summary>
    /// <param name="properties">The list of properties to map.</param>
    /// <param name="storageModel">The storage model to map from.</param>
    /// <param name="dataProperties">The payload properties on the data model.</param>
    /// <param name="vectorProperties">The vector properties on the data model.</param>
    /// <param name="hasNamedVectors">A value indicating whether qdrant is using named vectors for this collection.</param>
    public static void MapProperties(IEnumerable<VectorStoreRecordProperty> properties, PointStruct storageModel, Dictionary<string, object?> dataProperties, Dictionary<string, object?> vectorProperties, bool hasNamedVectors)
    {
        foreach (var property in properties)
        {
            if (property is VectorStoreRecordDataProperty dataProperty)
            {
                var storagePropertyName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;

                // Just skip this property if it's not in the storage model.
                if (!storageModel.Payload.TryGetValue(storagePropertyName, out var propertyValue))
                {
                    continue;
                }

                if (propertyValue.HasNullValue)
                {
                    // Shortcut any null handling here so we don't have to check for it for each case.
                    dataProperties[dataProperty.DataModelPropertyName] = null;
                }
                else
                {
                    var convertedValue = QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValueToNativeType(propertyValue, dataProperty.PropertyType);
                    dataProperties[dataProperty.DataModelPropertyName] = convertedValue;
                }
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                Vector? vector;
                if (hasNamedVectors)
                {
                    var storagePropertyName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;

                    // Just skip this property if it's not in the storage model.
                    if (!storageModel.Vectors.Vectors_.Vectors.TryGetValue(storagePropertyName, out vector))
                    {
                        continue;
                    }
                }
                else
                {
                    vector = storageModel.Vectors.Vector;
                }

                vectorProperties[vectorProperty.DataModelPropertyName] = new ReadOnlyMemory<float>(vector.Data.ToArray());
            }
        }
    }
}
