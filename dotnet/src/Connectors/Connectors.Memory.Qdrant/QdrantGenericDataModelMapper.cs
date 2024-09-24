// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.Data;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Qdrant.
/// </summary>
internal class QdrantGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<ulong>, PointStruct>, IVectorStoreRecordMapper<VectorStoreGenericDataModel<Guid>, PointStruct>
{
    /// <summary>A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    /// <summary>A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</summary>
    private readonly bool _hasNamedVectors;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantGenericDataModelMapper"/> class.
    /// </summary>
    /// <param name="vectorStoreRecordDefinition">The record definition that defines the schema of the record type.</param>
    /// <param name="hasNamedVectors">A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</param>
    public QdrantGenericDataModelMapper(
        VectorStoreRecordDefinition vectorStoreRecordDefinition,
        bool hasNamedVectors)
    {
        Verify.NotNull(vectorStoreRecordDefinition);

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify("VectorStoreGenericDataModel", vectorStoreRecordDefinition, supportsMultipleVectors: hasNamedVectors, requiresAtLeastOneVector: !hasNamedVectors);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.DataProperties, QdrantVectorStoreRecordFieldMapping.s_supportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.VectorProperties, QdrantVectorStoreRecordFieldMapping.s_supportedVectorTypes, "Vector");

        // Assign.
        this._vectorStoreRecordDefinition = vectorStoreRecordDefinition;
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
            this._vectorStoreRecordDefinition.Properties,
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
        MapProperties(this._vectorStoreRecordDefinition.Properties, storageModel, dataModel.Data, dataModel.Vectors, this._hasNamedVectors);
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
            this._vectorStoreRecordDefinition.Properties,
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
        MapProperties(this._vectorStoreRecordDefinition.Properties, storageModel, dataModel.Data, dataModel.Vectors, this._hasNamedVectors);
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
                else if (typeof(IEnumerable).IsAssignableFrom(dataProperty.PropertyType))
                {
                    // Using json deserialization to convert lists back into the correct enumerable type.
                    // There are many different possible enumerable types and this makes it easy to
                    // support all that System.Text.Json supports.
                    var jsonNode = QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValueToJsonNode(propertyValue);
                    var targetObject = jsonNode.Deserialize(dataProperty.PropertyType);
                    dataProperties[dataProperty.DataModelPropertyName] = targetObject;
                }
                else if (dataProperty.PropertyType == typeof(int) || dataProperty.PropertyType == typeof(int?))
                {
                    // The Qdrant sdk only returns long values for integers, so we need to convert them
                    // manually to the type of our data model.
                    var convertedValue = QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValue(propertyValue);
                    convertedValue = Convert.ToInt32(convertedValue);
                    dataProperties[dataProperty.DataModelPropertyName] = convertedValue;
                }
                else if (dataProperty.PropertyType == typeof(float) || dataProperty.PropertyType == typeof(float?))
                {
                    // The Qdrant sdk only returns double values for floats, so we need to convert them
                    // manually to the type of our data model.
                    var convertedValue = QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValue(propertyValue);
                    convertedValue = Convert.ToSingle(convertedValue);
                    dataProperties[dataProperty.DataModelPropertyName] = convertedValue;
                }
                else
                {
                    var convertedValue = QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValue(propertyValue);
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
