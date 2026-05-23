// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for mapping between a json node stored in redis, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
internal sealed class RedisJsonMapper<TConsumerDataModel>(
    CollectionModel model,
    JsonSerializerOptions jsonSerializerOptions)
    : IRedisJsonMapper<TConsumerDataModel>
    where TConsumerDataModel : class
{
    /// <summary>The key property.</summary>
    private readonly string _keyPropertyStorageName = model.KeyProperty.StorageName;

    /// <inheritdoc />
    public (string Key, JsonNode Node) MapFromDataToStorageModel(TConsumerDataModel dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        // Extract the key. The constructor has already validated that the key property is a string.
        var keyValue = model.KeyProperty.GetValueAsObject(dataModel) as string
            ?? throw new InvalidOperationException($"Missing key field '{this._keyPropertyStorageName}' on provided record of type {typeof(TConsumerDataModel).FullName}.");

        // Build the JSON payload from the model's data properties only, so that properties on the POCO that are not
        // part of the vector-store schema (no [VectorStoreData]/[VectorStoreVector]/[VectorStoreKey] attribute and not
        // in the collection definition) are not persisted in Redis.
        var jsonNode = new JsonObject();

        foreach (var dataProperty in model.DataProperties)
        {
            var value = dataProperty.GetValueAsObject(dataModel);
            jsonNode.Add(
                dataProperty.StorageName,
                value is null
                    ? null
                    : JsonSerializer.SerializeToNode(value, dataProperty.Type, jsonSerializerOptions));
        }

        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            var vector = generatedEmbeddings?[i]?[recordIndex] is Embedding ge
                ? (object)ge
                : property.GetValueAsObject(dataModel);

            if (vector is null)
            {
                jsonNode[property.StorageName] = null;
                continue;
            }

            var jsonArray = new JsonArray();

            if (vector switch
            {
                ReadOnlyMemory<float> m => m,
                Embedding<float> e => e.Vector,
                float[] a => new ReadOnlyMemory<float>(a),
                _ => (ReadOnlyMemory<float>?)null
            } is ReadOnlyMemory<float> floatMemory)
            {
                foreach (var item in floatMemory.Span)
                {
                    jsonArray.Add(JsonValue.Create(item));
                }
            }
            else if (vector switch
            {
                ReadOnlyMemory<double> m => m,
                Embedding<double> e => e.Vector,
                double[] a => new ReadOnlyMemory<double>(a),
                _ => null
            } is ReadOnlyMemory<double> doubleMemory)
            {
                foreach (var item in doubleMemory.Span)
                {
                    jsonArray.Add(JsonValue.Create(item));
                }
            }
            else
            {
                throw new UnreachableException();
            }

            jsonNode[property.StorageName] = jsonArray;
        }

        return (keyValue, jsonNode);
    }

    /// <inheritdoc />
    public TConsumerDataModel MapFromStorageToDataModel((string Key, JsonNode Node) storageModel, bool includeVectors)
    {
        // The redis result can have one of three different formats:
        // 1. a single object
        // 2. an array with a single object in the case where we are doing an MGET
        // 3. a single value (string, number, etc.) in the case where there is only one property being requested because the model has only one property apart from the key
        var jsonObject = storageModel.Node switch
        {
            JsonObject topLevelJsonObject => topLevelJsonObject,
            JsonArray and [JsonObject arrayEntryJsonObject] => arrayEntryJsonObject,
            JsonValue when model.DataProperties.Count + (includeVectors ? model.VectorProperties.Count : 0) == 1 => new JsonObject
            {
                [model.DataProperties.Concat<PropertyModel>(model.VectorProperties).First().StorageName] = storageModel.Node
            },
            _ => throw new InvalidOperationException($"Invalid data format for document with key '{storageModel.Key}'")
        };

        // Check that the key field is not already present in the redis value.
        if (jsonObject.ContainsKey(this._keyPropertyStorageName))
        {
            throw new InvalidOperationException($"Invalid data format for document with key '{storageModel.Key}'. Key property '{this._keyPropertyStorageName}' is already present on retrieved object.");
        }

        // Since the key is not stored in the redis value, add it back in before deserializing into the data model.
        jsonObject.Add(this._keyPropertyStorageName, storageModel.Key);

        // For vector properties which have embedding generation configured, we need to remove the embeddings before deserializing
        // (we can't go back from an embedding to e.g. string).
        if (includeVectors)
        {
            foreach (var vectorProperty in model.VectorProperties)
            {
                if (vectorProperty.Type == typeof(Embedding<float>) || vectorProperty.Type == typeof(Embedding<double>))
                {
                    var arrayNode = jsonObject[vectorProperty.StorageName];
                    if (arrayNode is not null)
                    {
                        var embeddingNode = new JsonObject
                        {
                            [nameof(Embedding<float>.Vector)] = arrayNode.DeepClone()
                        };
                        jsonObject[vectorProperty.StorageName] = embeddingNode;
                    }
                }
            }
        }
        else
        {
            foreach (var vectorProperty in model.VectorProperties)
            {
                jsonObject.Remove(vectorProperty.StorageName);
            }
        }

        return JsonSerializer.Deserialize<TConsumerDataModel>(jsonObject, jsonSerializerOptions)!;
    }
}
