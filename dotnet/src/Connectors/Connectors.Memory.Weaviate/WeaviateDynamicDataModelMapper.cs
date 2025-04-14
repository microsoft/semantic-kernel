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
internal sealed class WeaviateDynamicDataModelMapper : IWeaviateMapper<Dictionary<string, object?>>
{
    /// <summary>The name of the Weaviate collection.</summary>
    private readonly string _collectionName;

    /// <summary>The model.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>A <see cref="JsonSerializerOptions"/> for serialization/deserialization of record properties.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateDynamicDataModelMapper"/> class.
    /// </summary>
    /// <param name="collectionName">The name of the Weaviate collection</param>
    /// <param name="model">The model</param>
    /// <param name="jsonSerializerOptions">A <see cref="JsonSerializerOptions"/> for serialization/deserialization of record properties.</param>
    public WeaviateDynamicDataModelMapper(
        string collectionName,
        VectorStoreRecordModel model,
        JsonSerializerOptions jsonSerializerOptions)
    {
        this._collectionName = collectionName;
        this._model = model;
        this._jsonSerializerOptions = jsonSerializerOptions;
    }

    public JsonObject MapFromDataToStorageModel(Dictionary<string, object?> dataModel)
    {
        Verify.NotNull(dataModel);

        // Transform generic data model to Weaviate object model.
        var keyObject = JsonSerializer.SerializeToNode(dataModel[this._model.KeyProperty.ModelName]);

        // Populate data properties.
        var dataObject = new JsonObject();
        foreach (var property in this._model.DataProperties)
        {
            if (dataModel.TryGetValue(property.ModelName, out var dataValue))
            {
                dataObject[property.StorageName] = dataValue is null
                    ? null
                    : JsonSerializer.SerializeToNode(dataValue, property.Type, this._jsonSerializerOptions);
            }
        }

        // Populate vector properties.
        var vectorObject = new JsonObject();
        foreach (var property in this._model.VectorProperties)
        {
            if (dataModel.TryGetValue(property.ModelName, out var vectorValue))
            {
                vectorObject[property.StorageName] = vectorValue is null
                    ? null
                    : JsonSerializer.SerializeToNode(vectorValue, property.Type, this._jsonSerializerOptions);
            }
        }

        return new JsonObject
        {
            { WeaviateConstants.CollectionPropertyName, JsonValue.Create(this._collectionName) },
            { WeaviateConstants.ReservedKeyPropertyName, keyObject },
            { WeaviateConstants.ReservedDataPropertyName, dataObject },
            { WeaviateConstants.ReservedVectorPropertyName, vectorObject },
        };
    }

    public Dictionary<string, object?> MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        var result = new Dictionary<string, object?>();

        // Create variables to store the response properties.
        var key = storageModel[WeaviateConstants.ReservedKeyPropertyName]?.GetValue<Guid>();

        if (!key.HasValue)
        {
            throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
        }

        result[this._model.KeyProperty.ModelName] = key.Value;

        // Populate data properties.
        foreach (var property in this._model.DataProperties)
        {
            var jsonObject = storageModel[WeaviateConstants.ReservedDataPropertyName] as JsonObject;

            if (jsonObject is not null && jsonObject.TryGetPropertyValue(property.StorageName, out var dataValue))
            {
                result.Add(property.ModelName, dataValue.Deserialize(property.Type, this._jsonSerializerOptions));
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
                    result.Add(property.ModelName, vectorValue.Deserialize(property.Type, this._jsonSerializerOptions));
                }
            }
        }

        return result;
    }
}
