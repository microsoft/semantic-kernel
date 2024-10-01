// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Microsoft.SemanticKernel.Data;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Mapper between a Qdrant record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class QdrantVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, PointStruct>
    where TRecord : class
{
    /// <summary>The public parameterless constructor for the current data model.</summary>
    private readonly ConstructorInfo _constructorInfo;

    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>A list of property info objects that point at the data properties in the current model, and allows easy reading and writing of these properties.</summary>
    private readonly List<PropertyInfo> _dataPropertiesInfo;

    /// <summary>A list of property info objects that point at the vector properties in the current model, and allows easy reading and writing of these properties.</summary>
    private readonly List<PropertyInfo> _vectorPropertiesInfo;

    /// <summary>A dictionary that maps from a property name to the configured name that should be used when storing it.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames;

    /// <summary>A dictionary that maps from a property name to the configured name that should be used when serializing it to json.</summary>
    private readonly Dictionary<string, string> _jsonPropertyNames = new();

    /// <summary>A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</summary>
    private readonly bool _hasNamedVectors;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreRecordMapper{TDataModel}"/> class.
    /// </summary>
    /// <param name="vectorStoreRecordDefinition">The record definition that defines the schema of the record type.</param>
    /// <param name="hasNamedVectors">A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the configured name that should be used when storing it.</param>
    public QdrantVectorStoreRecordMapper(
        VectorStoreRecordDefinition vectorStoreRecordDefinition,
        bool hasNamedVectors,
        Dictionary<string, string> storagePropertyNames)
    {
        Verify.NotNull(vectorStoreRecordDefinition);
        Verify.NotNull(storagePropertyNames);

        // Validate property types.
        this._constructorInfo = VectorStoreRecordPropertyReader.GetParameterlessConstructor(typeof(TRecord));
        var propertiesInfo = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), vectorStoreRecordDefinition, supportsMultipleVectors: hasNamedVectors);
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(propertiesInfo.DataProperties, QdrantVectorStoreRecordFieldMapping.s_supportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(propertiesInfo.VectorProperties, QdrantVectorStoreRecordFieldMapping.s_supportedVectorTypes, "Vector");

        // Assign.
        this._hasNamedVectors = hasNamedVectors;
        this._keyPropertyInfo = propertiesInfo.KeyProperty;
        this._dataPropertiesInfo = propertiesInfo.DataProperties;
        this._vectorPropertiesInfo = propertiesInfo.VectorProperties;
        this._storagePropertyNames = storagePropertyNames;

        // Get json storage names and store for later use.
        this._jsonPropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToJsonPropertyNameMap(propertiesInfo, typeof(TRecord), JsonSerializerOptions.Default);
    }

    /// <inheritdoc />
    public PointStruct MapFromDataToStorageModel(TRecord dataModel)
    {
        PointId pointId;
        if (this._keyPropertyInfo.PropertyType == typeof(ulong))
        {
            var key = this._keyPropertyInfo.GetValue(dataModel) as ulong? ?? throw new VectorStoreRecordMappingException($"Missing key property {this._keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName}.");
            pointId = new PointId { Num = key };
        }
        else if (this._keyPropertyInfo.PropertyType == typeof(Guid))
        {
            var key = this._keyPropertyInfo.GetValue(dataModel) as Guid? ?? throw new VectorStoreRecordMappingException($"Missing key property {this._keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName}.");
            pointId = new PointId { Uuid = key.ToString("D") };
        }
        else
        {
            throw new VectorStoreRecordMappingException($"Unsupported key type {this._keyPropertyInfo.PropertyType.FullName} for key property {this._keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName}.");
        }

        // Create point.
        var pointStruct = new PointStruct
        {
            Id = pointId,
            Vectors = new Vectors(),
            Payload = { },
        };

        // Add point payload.
        foreach (var dataPropertyInfo in this._dataPropertiesInfo)
        {
            var propertyName = this._storagePropertyNames[dataPropertyInfo.Name];
            var propertyValue = dataPropertyInfo.GetValue(dataModel);
            pointStruct.Payload.Add(propertyName, QdrantVectorStoreRecordFieldMapping.ConvertToGrpcFieldValue(propertyValue));
        }

        // Add vectors.
        if (this._hasNamedVectors)
        {
            var namedVectors = new NamedVectors();
            foreach (var vectorPropertyInfo in this._vectorPropertiesInfo)
            {
                var propertyName = this._storagePropertyNames[vectorPropertyInfo.Name];
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
            var vectorPropertyInfo = this._vectorPropertiesInfo.First();
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
        var outputRecord = (TRecord)this._constructorInfo.Invoke(null);

        // Set Key.
        var keyPropertyInfoWithValue = new KeyValuePair<PropertyInfo, object?>(
                this._keyPropertyInfo,
                keyPropertyValue);
        VectorStoreRecordMapping.SetPropertiesOnRecord(
            outputRecord,
            [keyPropertyInfoWithValue]);

        // Set each vector property if embeddings are included in the point.
        if (options?.IncludeVectors is true)
        {
            if (this._hasNamedVectors)
            {
                var propertiesInfoWithValues = VectorStoreRecordMapping.BuildPropertiesInfoWithValues(
                    this._vectorPropertiesInfo,
                    this._storagePropertyNames,
                    storageModel.Vectors.Vectors_.Vectors,
                    (Vector vector, Type targetType) => new ReadOnlyMemory<float>(vector.Data.ToArray()));
                VectorStoreRecordMapping.SetPropertiesOnRecord(outputRecord, propertiesInfoWithValues);
            }
            else
            {
                var propertyInfoWithValue = new KeyValuePair<PropertyInfo, object?>(
                        this._vectorPropertiesInfo[0],
                        new ReadOnlyMemory<float>(storageModel.Vectors.Vector.Data.ToArray()));
                VectorStoreRecordMapping.SetPropertiesOnRecord(
                    outputRecord,
                    [propertyInfoWithValue]);
            }
        }

        // Set each data property.
        foreach (var dataProperty in this._dataPropertiesInfo)
        {
            var propertiesInfoWithValues = VectorStoreRecordMapping.BuildPropertiesInfoWithValues(
                this._dataPropertiesInfo,
                this._storagePropertyNames,
                storageModel.Payload,
                (Value grpcValue, Type targetType) =>
                    QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValueToNativeType(grpcValue, targetType));
            VectorStoreRecordMapping.SetPropertiesOnRecord(outputRecord, propertiesInfoWithValues);
        }

        return outputRecord;
    }
}
