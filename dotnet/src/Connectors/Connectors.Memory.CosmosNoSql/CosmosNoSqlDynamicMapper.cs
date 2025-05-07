﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData.ProviderServices;
using MEAI = Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Azure CosmosDB NoSQL.
/// </summary>
internal sealed class CosmosNoSqlDynamicMapper(CollectionModel model, JsonSerializerOptions jsonSerializerOptions)
    : ICosmosNoSqlMapper<Dictionary<string, object?>>
{
    /// <summary>A default <see cref="JsonSerializerOptions"/> for serialization/deserialization of vector properties.</summary>
    private static readonly JsonSerializerOptions s_vectorJsonSerializerOptions = new()
    {
        Converters = { new CosmosNoSqlReadOnlyMemoryByteConverter() }
    };

    public JsonObject MapFromDataToStorageModel(Dictionary<string, object?> dataModel, int recordIndex, IReadOnlyList<MEAI.Embedding>?[]? generatedEmbeddings)
    {
        Verify.NotNull(dataModel);

        var jsonObject = new JsonObject();

        jsonObject[CosmosNoSqlConstants.ReservedKeyPropertyName] = !dataModel.TryGetValue(model.KeyProperty.ModelName, out var keyValue)
            ? throw new InvalidOperationException($"Missing value for key property '{model.KeyProperty.ModelName}")
            : keyValue switch
            {
                string s => s,
                null => throw new InvalidOperationException($"Key property '{model.KeyProperty.ModelName}' is null."),
                _ => throw new InvalidCastException($"Key property '{model.KeyProperty.ModelName}' must be a string.")
            };

        foreach (var dataProperty in model.DataProperties)
        {
            if (dataModel.TryGetValue(dataProperty.StorageName, out var dataValue))
            {
                jsonObject[dataProperty.StorageName] = dataValue is not null ?
                    JsonSerializer.SerializeToNode(dataValue, dataProperty.Type, jsonSerializerOptions) :
                    null;
            }
        }

        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            if (generatedEmbeddings?[i]?[recordIndex] is MEAI.Embedding embedding)
            {
                Debug.Assert(property.EmbeddingGenerator is not null);

                jsonObject.Add(
                    property.StorageName,
                    embedding switch
                    {
                        MEAI.Embedding<float> e => JsonSerializer.SerializeToNode(e.Vector, s_vectorJsonSerializerOptions),
                        MEAI.Embedding<byte> e => JsonSerializer.SerializeToNode(e.Vector, s_vectorJsonSerializerOptions),
                        MEAI.Embedding<sbyte> e => JsonSerializer.SerializeToNode(e.Vector, s_vectorJsonSerializerOptions),
                        _ => throw new UnreachableException()
                    });
            }
            else
            {
                // No generated embedding, read the vector directly from the data model
                if (dataModel.TryGetValue(property.ModelName, out var sourceValue))
                {
                    jsonObject.Add(property.StorageName, sourceValue is null
                        ? null
                        : JsonSerializer.SerializeToNode(sourceValue, property.Type, s_vectorJsonSerializerOptions));
                }
            }
        }

        return jsonObject;
    }

    public Dictionary<string, object?> MapFromStorageToDataModel(JsonObject storageModel, bool includeVectors)
    {
        Verify.NotNull(storageModel);

        var result = new Dictionary<string, object?>();

        // Loop through all known properties and map each from the storage model to the data model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case KeyPropertyModel keyProperty:
                    result[keyProperty.ModelName] = storageModel.TryGetPropertyValue(CosmosNoSqlConstants.ReservedKeyPropertyName, out var keyValue)
                        ? keyValue?.GetValue<string>()
                        : throw new InvalidOperationException("No key property was found in the record retrieved from storage.");
                    continue;

                case DataPropertyModel dataProperty:
                    if (storageModel.TryGetPropertyValue(dataProperty.StorageName, out var dataValue))
                    {
                        result.Add(property.ModelName, dataValue.Deserialize(property.Type, jsonSerializerOptions));
                    }
                    continue;

                case VectorPropertyModel vectorProperty:
                    if (includeVectors && storageModel.TryGetPropertyValue(vectorProperty.StorageName, out var vectorValue))
                    {
                        result.Add(property.ModelName, vectorValue.Deserialize(property.Type, s_vectorJsonSerializerOptions));
                    }
                    continue;

                default:
                    throw new UnreachableException();
            }
        }

        return result;
    }
}
