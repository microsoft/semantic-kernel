// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Redis when using JSON.
/// </summary>
internal class RedisJsonDynamicMapper(CollectionModel model, JsonSerializerOptions jsonSerializerOptions) : IRedisJsonMapper<Dictionary<string, object?>>
{
    /// <inheritdoc />
    public (string Key, JsonNode Node) MapFromDataToStorageModel(Dictionary<string, object?> dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        var jsonObject = new JsonObject();

        // Key handled below, outside of the JsonNode

        foreach (var dataProperty in model.DataProperties)
        {
            if (dataModel.TryGetValue(dataProperty.ModelName, out var sourceValue))
            {
                jsonObject.Add(dataProperty.StorageName, sourceValue is null
                    ? null
                    : JsonSerializer.SerializeToNode(sourceValue, dataProperty.Type, jsonSerializerOptions));
            }
        }

        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            // Don't create a property if it doesn't exist in the dictionary
            if (dataModel.TryGetValue(property.ModelName, out var vectorValue))
            {
                var vector = generatedEmbeddings?[i]?[recordIndex] is Embedding ge
                    ? ge
                    : vectorValue;

                if (vector is null)
                {
                    jsonObject[property.StorageName] = null;
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

                jsonObject.Add(property.StorageName, jsonArray);
            }
        }

        return ((string)dataModel[model.KeyProperty.ModelName]!, jsonObject);
    }

    /// <inheritdoc />
    public Dictionary<string, object?> MapFromStorageToDataModel((string Key, JsonNode Node) storageModel, bool includeVectors)
    {
        var dataModel = new Dictionary<string, object?>
        {
            [model.KeyProperty.ModelName] = storageModel.Key,
        };

        // The redis result can be either a single object or an array with a single object in the case where we are doing an MGET.
        var jsonObject = storageModel.Node switch
        {
            JsonObject topLevelJsonObject => topLevelJsonObject,
            JsonArray jsonArray and [JsonObject arrayEntryJsonObject] => arrayEntryJsonObject,
            _ => throw new InvalidOperationException($"Invalid data format for document with key '{storageModel.Key}'"),
        };

        // The key was handled above

        foreach (var dataProperty in model.DataProperties)
        {
            // Replicate null if the property exists but is null.
            if (jsonObject.TryGetPropertyValue(dataProperty.StorageName, out var sourceValue))
            {
                dataModel.Add(dataProperty.ModelName, sourceValue is null
                   ? null
                   : JsonSerializer.Deserialize(sourceValue, dataProperty.Type, jsonSerializerOptions));
            }
        }

        if (includeVectors)
        {
            foreach (var vectorProperty in model.VectorProperties)
            {
                // Replicate null if the property exists but is null.
                if (jsonObject.TryGetPropertyValue(vectorProperty.StorageName, out var sourceValue))
                {
                    if (sourceValue is null)
                    {
                        dataModel.Add(vectorProperty.ModelName, null);
                        continue;
                    }

                    dataModel.Add(
                        vectorProperty.ModelName,
                        (Nullable.GetUnderlyingType(vectorProperty.Type) ?? vectorProperty.Type) switch
                        {
                            Type t when t == typeof(ReadOnlyMemory<float>) => new ReadOnlyMemory<float>(ToArray<float>(sourceValue)),
                            Type t when t == typeof(Embedding<float>) => new Embedding<float>(ToArray<float>(sourceValue)),
                            Type t when t == typeof(float[]) => ToArray<float>(sourceValue),

                            Type t when t == typeof(ReadOnlyMemory<double>) => new ReadOnlyMemory<double>(ToArray<double>(sourceValue)),
                            Type t when t == typeof(Embedding<double>) => new Embedding<double>(ToArray<double>(sourceValue)),
                            Type t when t == typeof(double[]) => ToArray<double>(sourceValue),

                            _ => throw new UnreachableException()
                        });
                }
            }
        }

        return dataModel;

        static T[] ToArray<T>(JsonNode jsonNode)
        {
            var jsonArray = jsonNode.AsArray();
            var array = new T[jsonArray.Count];

            for (var i = 0; i < jsonArray.Count; i++)
            {
                array[i] = jsonArray[i]!.GetValue<T>();
            }

            return array;
        }
    }
}
