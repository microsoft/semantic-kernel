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
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
internal sealed class WeaviateDynamicDataModelMapper : IVectorStoreRecordMapper<Dictionary<string, object?>, JsonObject>
#pragma warning restore CS0618
{
    /// <summary>The name of the Weaviate collection.</summary>
    private readonly string _collectionName;

    /// <summary>The model.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>A <see cref="JsonSerializerOptions"/> for serialization/deserialization of record properties.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>Gets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector in Weaviate collection.</summary>
    private readonly bool _hasNamedVectors;

    /// <summary>Gets a vector property named used in Weaviate collection.</summary>
    private readonly string _vectorPropertyName;

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateDynamicDataModelMapper"/> class.
    /// </summary>
    /// <param name="collectionName">The name of the Weaviate collection</param>
    /// <param name="hasNamedVectors">Gets or sets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector in Weaviate collection</param>
    /// <param name="model">The model</param>
    /// <param name="jsonSerializerOptions">A <see cref="JsonSerializerOptions"/> for serialization/deserialization of record properties.</param>
    public WeaviateDynamicDataModelMapper(
        string collectionName,
        bool hasNamedVectors,
        VectorStoreRecordModel model,
        JsonSerializerOptions jsonSerializerOptions)
    {
        this._collectionName = collectionName;
        this._hasNamedVectors = hasNamedVectors;
        this._model = model;
        this._jsonSerializerOptions = jsonSerializerOptions;

        this._vectorPropertyName = hasNamedVectors ?
            WeaviateConstants.ReservedVectorPropertyName :
            WeaviateConstants.ReservedSingleVectorPropertyName;
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
        JsonNode? vectorObject = null;

        if (this._hasNamedVectors)
        {
            vectorObject = new JsonObject();
            foreach (var property in this._model.VectorProperties)
            {
                if (dataModel.TryGetValue(property.ModelName, out var vectorValue))
                {
                    vectorObject[property.StorageName] = vectorValue is null
                        ? null
                        : JsonSerializer.SerializeToNode(vectorValue, property.Type, this._jsonSerializerOptions);
                }
            }
        }
        else
        {
            if (dataModel.TryGetValue(this._model.VectorProperty.ModelName, out var vectorValue))
            {
                vectorObject = vectorValue is null
                    ? null
                    : JsonSerializer.SerializeToNode(vectorValue, this._model.VectorProperty.Type, this._jsonSerializerOptions);
            }
        }

        return new JsonObject
        {
            { WeaviateConstants.CollectionPropertyName, JsonValue.Create(this._collectionName) },
            { WeaviateConstants.ReservedKeyPropertyName, keyObject },
            { WeaviateConstants.ReservedDataPropertyName, dataObject },
            { this._vectorPropertyName, vectorObject },
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
            if (this._hasNamedVectors)
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
            else
            {
                var jsonObject = storageModel[WeaviateConstants.ReservedSingleVectorPropertyName];

                if (jsonObject is not null)
                {
                    result.Add(this._model.VectorProperty.ModelName, jsonObject.Deserialize(this._model.VectorProperty.Type, this._jsonSerializerOptions));
                }
            }
        }

        return result;
    }
}
