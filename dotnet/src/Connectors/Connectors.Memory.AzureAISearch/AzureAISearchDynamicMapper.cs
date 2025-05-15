// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;
using MEAI = Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Azure AI Search.
/// </summary>
internal sealed class AzureAISearchDynamicMapper(CollectionModel model, JsonSerializerOptions? jsonSerializerOptions) : IAzureAISearchMapper<Dictionary<string, object?>>
{
    /// <inheritdoc />
    public JsonObject MapFromDataToStorageModel(Dictionary<string, object?> dataModel, int recordIndex, IReadOnlyList<MEAI.Embedding>?[]? generatedEmbeddings)
    {
        Verify.NotNull(dataModel);

        var jsonObject = new JsonObject();

        jsonObject[model.KeyProperty.StorageName] = !dataModel.TryGetValue(model.KeyProperty.ModelName, out var keyValue)
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

                var memory = vector switch
                {
                    ReadOnlyMemory<float> m => m,
                    Embedding<float> e => e.Vector,
                    float[] a => a,

                    _ => throw new UnreachableException()
                };

                var jsonArray = new JsonArray();

                foreach (var item in memory.Span)
                {
                    jsonArray.Add(JsonValue.Create(item));
                }

                jsonObject.Add(property.StorageName, jsonArray);
            }
        }

        return jsonObject;
    }

    /// <inheritdoc />
    public Dictionary<string, object?> MapFromStorageToDataModel(JsonObject storageModel, bool includeVectors)
    {
        Verify.NotNull(storageModel);

        // Create variables to store the response properties.
        var result = new Dictionary<string, object?>();

        // Loop through all known properties and map each from json to the data type.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case KeyPropertyModel keyProperty:
                    result[keyProperty.ModelName] = (string?)storageModel[keyProperty.StorageName]
                        ?? throw new InvalidOperationException($"The key property '{keyProperty.StorageName}' is missing from the record retrieved from storage.");

                    continue;

                case DataPropertyModel dataProperty:
                {
                    if (storageModel.TryGetPropertyValue(dataProperty.StorageName, out var value))
                    {
                        result.Add(dataProperty.ModelName, value is null ? null : GetDataPropertyValue(property.Type, value));
                    }
                    continue;
                }

                case VectorPropertyModel vectorProperty when includeVectors:
                {
                    if (storageModel.TryGetPropertyValue(vectorProperty.StorageName, out var value))
                    {
                        if (value is null)
                        {
                            result.Add(vectorProperty.ModelName, null);
                            continue;
                        }

                        var vector = value.AsArray().Select(x => (float)x!).ToArray();
                        result.Add(
                            vectorProperty.ModelName,
                            (Nullable.GetUnderlyingType(vectorProperty.Type) ?? vectorProperty.Type) switch
                            {
                                Type t when t == typeof(ReadOnlyMemory<float>) => new ReadOnlyMemory<float>(vector),
                                Type t when t == typeof(Embedding<float>) => new Embedding<float>(vector),
                                Type t when t == typeof(float[]) => vector,

                                _ => throw new UnreachableException()
                            });
                    }

                    continue;
                }

                case VectorPropertyModel vectorProperty when !includeVectors:
                    break;

                default:
                    throw new UnreachableException();
            }
        }

        return result;
    }

    /// <summary>
    /// Get the value of the given json node as the given property type.
    /// </summary>
    /// <param name="propertyType">The type of property that is required.</param>
    /// <param name="value">The json node containing the property value.</param>
    /// <returns>The value of the json node as the required type.</returns>
    private static object? GetDataPropertyValue(Type propertyType, JsonNode value)
    {
        var result = propertyType switch
        {
            Type t when t == typeof(string) => value.GetValue<string>(),
            Type t when t == typeof(int) => value.GetValue<int>(),
            Type t when t == typeof(int?) => value.GetValue<int?>(),
            Type t when t == typeof(long) => value.GetValue<long>(),
            Type t when t == typeof(long?) => value.GetValue<long?>(),
            Type t when t == typeof(float) => value.GetValue<float>(),
            Type t when t == typeof(float?) => value.GetValue<float?>(),
            Type t when t == typeof(double) => value.GetValue<double>(),
            Type t when t == typeof(double?) => value.GetValue<double?>(),
            Type t when t == typeof(bool) => value.GetValue<bool>(),
            Type t when t == typeof(bool?) => value.GetValue<bool?>(),
            Type t when t == typeof(DateTime) => value.GetValue<DateTime>(),
            Type t when t == typeof(DateTime?) => value.GetValue<DateTime?>(),
            Type t when t == typeof(DateTimeOffset) => value.GetValue<DateTimeOffset>(),
            Type t when t == typeof(DateTimeOffset?) => value.GetValue<DateTimeOffset?>(),

            _ => (object?)null
        };

        if (result is not null)
        {
            return result;
        }

        if (propertyType.IsArray)
        {
            return propertyType switch
            {
                Type t when t == typeof(string[]) => value.AsArray().Select(x => (string?)x).ToArray(),
                Type t when t == typeof(int[]) => value.AsArray().Select(x => (int)x!).ToArray(),
                Type t when t == typeof(int?[]) => value.AsArray().Select(x => (int?)x).ToArray(),
                Type t when t == typeof(long[]) => value.AsArray().Select(x => (long)x!).ToArray(),
                Type t when t == typeof(long?[]) => value.AsArray().Select(x => (long?)x).ToArray(),
                Type t when t == typeof(float[]) => value.AsArray().Select(x => (float)x!).ToArray(),
                Type t when t == typeof(float?[]) => value.AsArray().Select(x => (float?)x).ToArray(),
                Type t when t == typeof(double[]) => value.AsArray().Select(x => (double)x!).ToArray(),
                Type t when t == typeof(double?[]) => value.AsArray().Select(x => (double?)x).ToArray(),
                Type t when t == typeof(bool[]) => value.AsArray().Select(x => (bool)x!).ToArray(),
                Type t when t == typeof(bool?[]) => value.AsArray().Select(x => (bool?)x).ToArray(),
                Type t when t == typeof(DateTime[]) => value.AsArray().Select(x => (DateTime)x!).ToArray(),
                Type t when t == typeof(DateTime?[]) => value.AsArray().Select(x => (DateTime?)x).ToArray(),
                Type t when t == typeof(DateTimeOffset[]) => value.AsArray().Select(x => (DateTimeOffset)x!).ToArray(),
                Type t when t == typeof(DateTimeOffset?[]) => value.AsArray().Select(x => (DateTimeOffset?)x).ToArray(),

                _ => throw new UnreachableException($"Unsupported property type '{propertyType.Name}'.")
            };
        }

        if (propertyType.IsGenericType && propertyType.GetGenericTypeDefinition() == typeof(List<>))
        {
            return propertyType switch
            {
                Type t when t == typeof(List<string>) => value.AsArray().Select(x => (string?)x).ToList(),
                Type t when t == typeof(List<int>) => value.AsArray().Select(x => (int)x!).ToList(),
                Type t when t == typeof(List<int?>) => value.AsArray().Select(x => (int?)x).ToList(),
                Type t when t == typeof(List<long>) => value.AsArray().Select(x => (long)x!).ToList(),
                Type t when t == typeof(List<long?>) => value.AsArray().Select(x => (long?)x).ToList(),
                Type t when t == typeof(List<float>) => value.AsArray().Select(x => (float)x!).ToList(),
                Type t when t == typeof(List<float?>) => value.AsArray().Select(x => (float?)x).ToList(),
                Type t when t == typeof(List<double>) => value.AsArray().Select(x => (double)x!).ToList(),
                Type t when t == typeof(List<double?>) => value.AsArray().Select(x => (double?)x).ToList(),
                Type t when t == typeof(List<bool>) => value.AsArray().Select(x => (bool)x!).ToList(),
                Type t when t == typeof(List<bool?>) => value.AsArray().Select(x => (bool?)x).ToList(),
                Type t when t == typeof(List<DateTime>) => value.AsArray().Select(x => (DateTime)x!).ToList(),
                Type t when t == typeof(List<DateTime?>) => value.AsArray().Select(x => (DateTime?)x).ToList(),
                Type t when t == typeof(List<DateTimeOffset>) => value.AsArray().Select(x => (DateTimeOffset)x!).ToList(),
                Type t when t == typeof(List<DateTimeOffset?>) => value.AsArray().Select(x => (DateTimeOffset?)x).ToList(),

                _ => throw new UnreachableException($"Unsupported property type '{propertyType.Name}'.")
            };
        }

        throw new UnreachableException($"Unsupported property type '{propertyType.Name}'.");
    }
}
