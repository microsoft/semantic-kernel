// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;
using MEAI = Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Azure CosmosDB NoSQL.
/// </summary>
internal sealed class CosmosNoSqlDynamicMapper(CollectionModel model, JsonSerializerOptions jsonSerializerOptions)
    : ICosmosNoSqlMapper<Dictionary<string, object?>>
{
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
            if (dataModel.TryGetValue(dataProperty.ModelName, out var dataValue))
            {
                jsonObject[dataProperty.StorageName] = dataValue is not null ?
                    JsonSerializer.SerializeToNode(dataValue, dataProperty.Type, jsonSerializerOptions) :
                    null;
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

                switch (vector)
                {
                    case var _ when TryGetReadOnlyMemory<float>(vector, out var floatMemory):
                        foreach (var item in floatMemory.Value.Span)
                        {
                            jsonArray.Add(JsonValue.Create(item));
                        }
                        break;

                    case var _ when TryGetReadOnlyMemory<byte>(vector, out var byteMemory):
                        foreach (var item in byteMemory.Value.Span)
                        {
                            jsonArray.Add(JsonValue.Create(item));
                        }
                        break;

                    case var _ when TryGetReadOnlyMemory<sbyte>(vector, out var sbyteMemory):
                        foreach (var item in sbyteMemory.Value.Span)
                        {
                            jsonArray.Add(JsonValue.Create(item));
                        }
                        break;

                    default:
                        throw new UnreachableException();
                }

                jsonObject.Add(property.StorageName, jsonArray);
            }
        }

        return jsonObject;

        static bool TryGetReadOnlyMemory<T>(object value, [NotNullWhen(true)] out ReadOnlyMemory<T>? memory)
        {
            memory = value switch
            {
                ReadOnlyMemory<T> m => m,
                Embedding<T> e => e.Vector,
                T[] a => a,
                _ => (ReadOnlyMemory<T>?)null
            };

            return memory is not null;
        }
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
                        if (vectorValue is not null)
                        {
                            result.Add(
                                vectorProperty.ModelName,
                                (Nullable.GetUnderlyingType(vectorProperty.Type) ?? vectorProperty.Type) switch
                                {
                                    Type t when t == typeof(ReadOnlyMemory<float>) => new ReadOnlyMemory<float>(ToArray<float>(vectorValue)),
                                    Type t when t == typeof(Embedding<float>) => new Embedding<float>(ToArray<float>(vectorValue)),
                                    Type t when t == typeof(float[]) => ToArray<float>(vectorValue),

                                    Type t when t == typeof(ReadOnlyMemory<byte>) => new ReadOnlyMemory<byte>(ToArray<byte>(vectorValue)),
                                    Type t when t == typeof(Embedding<byte>) => new Embedding<byte>(ToArray<byte>(vectorValue)),
                                    Type t when t == typeof(byte[]) => ToArray<byte>(vectorValue),

                                    Type t when t == typeof(ReadOnlyMemory<sbyte>) => new ReadOnlyMemory<sbyte>(ToArray<sbyte>(vectorValue)),
                                    Type t when t == typeof(Embedding<sbyte>) => new Embedding<sbyte>(ToArray<sbyte>(vectorValue)),
                                    Type t when t == typeof(sbyte[]) => ToArray<sbyte>(vectorValue),

                                    _ => throw new UnreachableException()
                                });
                        }
                        else
                        {
                            result.Add(vectorProperty.ModelName, null);
                        }
                    }
                    continue;

                default:
                    throw new UnreachableException();
            }
        }

        return result;

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
