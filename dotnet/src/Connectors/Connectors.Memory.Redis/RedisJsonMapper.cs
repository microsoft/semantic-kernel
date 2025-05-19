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
        // Convert the provided record into a JsonNode object and try to get the key field for it.
        // Since we already checked that the key field is a string in the constructor, and that it exists on the model,
        // the only edge case we have to be concerned about is if the key field is null.
        var jsonNode = JsonSerializer.SerializeToNode(dataModel, jsonSerializerOptions)!.AsObject();

        if (!(jsonNode.TryGetPropertyValue(this._keyPropertyStorageName, out var keyField) && keyField is JsonValue jsonValue))
        {
            throw new InvalidOperationException($"Missing key field '{this._keyPropertyStorageName}' on provided record of type {typeof(TConsumerDataModel).FullName}.");
        }

        // Remove the key field from the JSON object since we don't want to store it in the redis payload.
        var keyValue = jsonValue.ToString();
        jsonNode.Remove(this._keyPropertyStorageName);

        // Go over the vector properties; inject any generated embeddings to overwrite the JSON serialized above.
        // Also, for Embedding<T> properties we also need to overwrite with a simple array (since Embedding<T> gets serialized as a complex object).
        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            Embedding? embedding = generatedEmbeddings?[i]?[recordIndex] is Embedding ge ? ge : null;

            if (embedding is null)
            {
                switch (Nullable.GetUnderlyingType(property.Type) ?? property.Type)
                {
                    case var t when t == typeof(ReadOnlyMemory<float>):
                    case var t2 when t2 == typeof(float[]):
                    case var t3 when t3 == typeof(ReadOnlyMemory<double>):
                    case var t4 when t4 == typeof(double[]):
                        // The .NET vector property is a ReadOnlyMemory<T> or T[] (not an Embedding), which means that JsonSerializer
                        // already serialized it correctly above.
                        // In addition, there's no generated embedding (which would be an Embedding which we'd need to handle manually).
                        // So there's nothing for us to do.
                        continue;

                    case var t when t == typeof(Embedding<float>):
                    case var t1 when t1 == typeof(Embedding<double>):
                        embedding = (Embedding)property.GetValueAsObject(dataModel)!;
                        break;

                    default:
                        throw new UnreachableException();
                }
            }

            var jsonArray = new JsonArray();

            switch (embedding)
            {
                case Embedding<float> e:
                    foreach (var item in e.Vector.Span)
                    {
                        jsonArray.Add(JsonValue.Create(item));
                    }
                    break;

                case Embedding<double> e:
                    foreach (var item in e.Vector.Span)
                    {
                        jsonArray.Add(JsonValue.Create(item));
                    }
                    break;

                default:
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
                        var embeddingNode = new JsonObject();
                        embeddingNode[nameof(Embedding<float>.Vector)] = arrayNode.DeepClone();
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
