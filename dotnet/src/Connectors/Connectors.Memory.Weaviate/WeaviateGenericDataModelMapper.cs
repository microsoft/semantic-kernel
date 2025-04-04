// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Weaviate.
/// </summary>
internal sealed class WeaviateGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<Guid>, JsonObject>
{
    /// <summary>The name of the Weaviate collection.</summary>
    private readonly string _collectionName;

    /// <summary>The model.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>A <see cref="JsonSerializerOptions"/> for serialization/deserialization of record properties.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateGenericDataModelMapper"/> class.
    /// </summary>
    /// <param name="collectionName">The name of the Weaviate collection</param>
    /// <param name="model">The model</param>
    /// <param name="jsonSerializerOptions">A <see cref="JsonSerializerOptions"/> for serialization/deserialization of record properties.</param>
    public WeaviateGenericDataModelMapper(
        string collectionName,
        VectorStoreRecordModel model,
        JsonSerializerOptions jsonSerializerOptions)
    {
        this._collectionName = collectionName;
        this._model = model;
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
        foreach (var property in this._model.DataProperties)
        {
            if (dataModel.Data is not null && dataModel.Data.TryGetValue(property.ModelName, out var dataValue))
            {
                weaviateObjectModel[WeaviateConstants.ReservedDataPropertyName]![property.StorageName] = dataValue is not null ?
                        JsonSerializer.SerializeToNode(dataValue, property.Type, this._jsonSerializerOptions) :
                        null;
            }
        }

        // Populate vector properties.
        foreach (var property in this._model.VectorProperties)
        {
            if (dataModel.Vectors is not null && dataModel.Vectors.TryGetValue(property.ModelName, out var vectorValue))
            {
                weaviateObjectModel[WeaviateConstants.ReservedVectorPropertyName]![property.StorageName] = vectorValue is not null ?
                        JsonSerializer.SerializeToNode(vectorValue, property.Type, this._jsonSerializerOptions) :
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
        foreach (var property in this._model.DataProperties)
        {
            var jsonObject = storageModel[WeaviateConstants.ReservedDataPropertyName] as JsonObject;

            if (jsonObject is not null && jsonObject.TryGetPropertyValue(property.StorageName, out var dataValue))
            {
                dataProperties.Add(property.ModelName, dataValue.Deserialize(property.Type, this._jsonSerializerOptions));
            }
        }

        // Populate vector properties.
        if (options.IncludeVectors)
        {
            foreach (var property in this._model.VectorProperties)
            {
                var jsonObject = storageModel[WeaviateConstants.ReservedVectorPropertyName] as JsonObject;

                if (jsonObject is not null && jsonObject.TryGetPropertyValue(property.StorageName, out var vectorValue))
                {
                    vectorProperties.Add(property.ModelName, vectorValue.Deserialize(property.Type, this._jsonSerializerOptions));
                }
            }
        }

        return new VectorStoreGenericDataModel<Guid>(key.Value) { Data = dataProperties, Vectors = vectorProperties };
    }
}
