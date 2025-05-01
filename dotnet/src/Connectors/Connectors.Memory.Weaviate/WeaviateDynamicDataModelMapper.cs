// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
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

    public JsonObject MapFromDataToStorageModel(Dictionary<string, object?> dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        Verify.NotNull(dataModel);

        // Transform generic data model to Weaviate object model.
        var keyNode = JsonSerializer.SerializeToNode(dataModel[this._model.KeyProperty.ModelName]);

        // Populate data properties.
        var dataNode = new JsonObject();
        foreach (var property in this._model.DataProperties)
        {
            if (dataModel.TryGetValue(property.ModelName, out var dataValue))
            {
                dataNode[property.StorageName] = dataValue is null
                    ? null
                    : JsonSerializer.SerializeToNode(dataValue, property.Type, this._jsonSerializerOptions);
            }
        }

        // Populate vector properties.
        JsonNode? vectorNode = null;

        if (this._hasNamedVectors)
        {
            vectorNode = new JsonObject();

            for (var i = 0; i < this._model.VectorProperties.Count; i++)
            {
                var property = this._model.VectorProperties[i];

                var vectorValue = generatedEmbeddings?[i] switch
                {
                    IReadOnlyList<Embedding<float>> e => e[recordIndex].Vector,
                    IReadOnlyList<Embedding<double>> e => e[recordIndex].Vector,
                    null => dataModel.TryGetValue(property.ModelName, out var v) ? v : null,
                    _ => throw new NotSupportedException($"Unsupported embedding type '{generatedEmbeddings?[i]?.GetType().Name}' for property '{property.ModelName}'.")
                };

                vectorNode[property.StorageName] = vectorValue is null
                    ? null
                    : JsonSerializer.SerializeToNode(vectorValue, property.EmbeddingType, this._jsonSerializerOptions);
            }
        }
        else
        {
            var vectorValue = generatedEmbeddings?[0] is IReadOnlyList<Embedding<float>> e
                ? e[recordIndex].Vector
                : dataModel.TryGetValue(this._model.VectorProperty.ModelName, out var v)
                    ? v
                    : null;

            vectorNode = vectorValue is null
                ? null
                : JsonSerializer.SerializeToNode(vectorValue, this._model.VectorProperty.EmbeddingType, this._jsonSerializerOptions);
        }

        return new JsonObject
        {
            { WeaviateConstants.CollectionPropertyName, JsonValue.Create(this._collectionName) },
            { WeaviateConstants.ReservedKeyPropertyName, keyNode },
            { WeaviateConstants.ReservedDataPropertyName, dataNode },
            { this._vectorPropertyName, vectorNode },
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
                var jsonNode = storageModel[WeaviateConstants.ReservedSingleVectorPropertyName];

                if (jsonNode is not null)
                {
                    result.Add(this._model.VectorProperty.ModelName, jsonNode.Deserialize(this._model.VectorProperty.Type, this._jsonSerializerOptions));
                }
            }
        }

        return result;
    }
}
