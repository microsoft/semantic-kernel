﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
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
        var propertiesInfo = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), vectorStoreRecordDefinition, supportsMultipleVectors: hasNamedVectors);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(propertiesInfo.DataProperties, QdrantVectorStoreRecordFieldMapping.s_supportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(propertiesInfo.VectorProperties, QdrantVectorStoreRecordFieldMapping.s_supportedVectorTypes, "Vector");

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
        var keyJsonName = this._jsonPropertyNames[this._keyPropertyInfo.Name];
        var keyPropertyValue = storageModel.Id.HasNum ? storageModel.Id.Num as object : storageModel.Id.Uuid as object;

        // Create a json object to represent the point.
        var outputJsonObject = new JsonObject
        {
            { keyJsonName, JsonValue.Create(keyPropertyValue) },
        };

        // Add each vector property if embeddings are included in the point.
        if (options?.IncludeVectors is true)
        {
            foreach (var vectorProperty in this._vectorPropertiesInfo)
            {
                var propertyName = this._storagePropertyNames[vectorProperty.Name];
                var jsonName = this._jsonPropertyNames[vectorProperty.Name];

                if (this._hasNamedVectors)
                {
                    if (storageModel.Vectors.Vectors_.Vectors.TryGetValue(propertyName, out var vector))
                    {
                        outputJsonObject.Add(jsonName, new JsonArray(vector.Data.Select(x => JsonValue.Create(x)).ToArray()));
                    }
                }
                else
                {
                    outputJsonObject.Add(jsonName, new JsonArray(storageModel.Vectors.Vector.Data.Select(x => JsonValue.Create(x)).ToArray()));
                }
            }
        }

        // Add each data property.
        foreach (var dataProperty in this._dataPropertiesInfo)
        {
            var propertyName = this._storagePropertyNames[dataProperty.Name];
            var jsonName = this._jsonPropertyNames[dataProperty.Name];

            if (storageModel.Payload.TryGetValue(propertyName, out var value))
            {
                outputJsonObject.Add(jsonName, QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValueToJsonNode(value));
            }
        }

        // Convert from json object to the target data model.
        return JsonSerializer.Deserialize<TRecord>(outputJsonObject)!;
    }
}
