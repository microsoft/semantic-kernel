// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Weaviate.
/// </summary>
internal sealed class WeaviateGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<Guid>, JsonObject>
{
    /// <summary>The name of the Weaviate collection.</summary>
    private readonly string _collectionName;

    /// <summary>A <see cref="VectorStoreRecordKeyProperty"/> property of record definition.</summary>
    private readonly VectorStoreRecordKeyProperty _keyProperty;

    /// <summary>A collection of <see cref="VectorStoreRecordDataProperty"/> properties of record definition.</summary>
    private readonly IReadOnlyList<VectorStoreRecordDataProperty> _dataProperties;

    /// <summary>A collection of <see cref="VectorStoreRecordVectorProperty"/> properties of record definition.</summary>
    private readonly IReadOnlyList<VectorStoreRecordVectorProperty> _vectorProperties;

    /// <summary>A dictionary that maps from a property name to the storage name.</summary>
    private readonly IReadOnlyDictionary<string, string> _storagePropertyNames;

    /// <summary>A <see cref="JsonSerializerOptions"/> for serialization/deserialization of record properties.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateGenericDataModelMapper"/> class.
    /// </summary>
    /// <param name="collectionName">The name of the Weaviate collection</param>
    /// <param name="keyProperty">A <see cref="VectorStoreRecordKeyProperty"/> property of record definition.</param>
    /// <param name="dataProperties">A collection of <see cref="VectorStoreRecordDataProperty"/> properties of record definition.</param>
    /// <param name="vectorProperties">A collection of <see cref="VectorStoreRecordVectorProperty"/> properties of record definition.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name.</param>
    /// <param name="jsonSerializerOptions">A <see cref="JsonSerializerOptions"/> for serialization/deserialization of record properties.</param>
    public WeaviateGenericDataModelMapper(
        string collectionName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordDataProperty> dataProperties,
        IReadOnlyList<VectorStoreRecordVectorProperty> vectorProperties,
        IReadOnlyDictionary<string, string> storagePropertyNames,
        JsonSerializerOptions jsonSerializerOptions)
    {
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(keyProperty);
        Verify.NotNull(dataProperties);
        Verify.NotNull(vectorProperties);
        Verify.NotNull(storagePropertyNames);
        Verify.NotNull(jsonSerializerOptions);

        this._collectionName = collectionName;
        this._keyProperty = keyProperty;
        this._dataProperties = dataProperties;
        this._vectorProperties = vectorProperties;
        this._storagePropertyNames = storagePropertyNames;
        this._jsonSerializerOptions = jsonSerializerOptions;
    }

    public JsonObject MapFromDataToStorageModel(VectorStoreGenericDataModel<Guid> dataModel)
    {
        Verify.NotNull(dataModel);

        // Transform generic data model to Weaviate object model.
        var weaviateObjectModel = new JsonObject
        {
            { WeaviateConstants.CollectionPropertyName, JsonValue.Create(this._collectionName) },
            { WeaviateConstants.ReservedKeyPropertyName, dataModel.Key },
            { WeaviateConstants.ReservedDataPropertyName, new JsonObject() },
            { WeaviateConstants.ReservedVectorPropertyName, new JsonObject() },
        };

        // Populate data properties.
        foreach (var property in this._dataProperties)
        {
            if (dataModel.Data is not null && dataModel.Data.TryGetValue(property.DataModelPropertyName, out var dataValue))
            {
                var storagePropertyName = this._storagePropertyNames[property.DataModelPropertyName];

                weaviateObjectModel[WeaviateConstants.ReservedDataPropertyName]![storagePropertyName] = dataValue is not null ?
                        JsonSerializer.SerializeToNode(dataValue, property.PropertyType, this._jsonSerializerOptions) :
                        null;
            }
        }

        // Populate vector properties.
        foreach (var property in this._vectorProperties)
        {
            if (dataModel.Vectors is not null && dataModel.Vectors.TryGetValue(property.DataModelPropertyName, out var vectorValue))
            {
                var storagePropertyName = this._storagePropertyNames[property.DataModelPropertyName];

                weaviateObjectModel[WeaviateConstants.ReservedVectorPropertyName]![storagePropertyName] = vectorValue is not null ?
                        JsonSerializer.SerializeToNode(vectorValue, property.PropertyType, this._jsonSerializerOptions) :
                        null;
            }
        }

        return weaviateObjectModel;
    }

    public VectorStoreGenericDataModel<Guid> MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        // Create variables to store the response properties.
        var key = storageModel[WeaviateConstants.ReservedKeyPropertyName]?.GetValue<Guid>();

        if (!key.HasValue)
        {
            throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
        }

        var dataProperties = new Dictionary<string, object?>();
        var vectorProperties = new Dictionary<string, object?>();

        // Populate data properties.
        foreach (var property in this._dataProperties)
        {
            var storagePropertyName = this._storagePropertyNames[property.DataModelPropertyName];
            var jsonObject = storageModel[WeaviateConstants.ReservedDataPropertyName] as JsonObject;

            if (jsonObject is not null && jsonObject.TryGetPropertyValue(storagePropertyName, out var dataValue))
            {
                dataProperties.Add(property.DataModelPropertyName, dataValue.Deserialize(property.PropertyType, this._jsonSerializerOptions));
            }
        }

        // Populate vector properties.
        if (options.IncludeVectors)
        {
            foreach (var property in this._vectorProperties)
            {
                var storagePropertyName = this._storagePropertyNames[property.DataModelPropertyName];
                var jsonObject = storageModel[WeaviateConstants.ReservedVectorPropertyName] as JsonObject;

                if (jsonObject is not null && jsonObject.TryGetPropertyValue(storagePropertyName, out var vectorValue))
                {
                    vectorProperties.Add(property.DataModelPropertyName, vectorValue.Deserialize(property.PropertyType, this._jsonSerializerOptions));
                }
            }
        }

        return new VectorStoreGenericDataModel<Guid>(key.Value) { Data = dataProperties, Vectors = vectorProperties };
    }
}
