// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
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

            if (generatedEmbeddings?[i]?[recordIndex] is MEAI.Embedding embedding)
            {
                Debug.Assert(property.EmbeddingGenerator is not null);

                jsonObject.Add(
                    property.StorageName,
                    embedding switch
                    {
                        MEAI.Embedding<float> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
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
                        : JsonSerializer.SerializeToNode(sourceValue, property.Type, jsonSerializerOptions));
                }
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
                        if (value is not null)
                        {
                            ReadOnlyMemory<float> vector = value.AsArray().Select(x => (float)x!).ToArray();
                            result.Add(vectorProperty.ModelName, vector);
                        }
                        else
                        {
                            result.Add(vectorProperty.ModelName, null);
                        }
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
        if (propertyType == typeof(string))
        {
            return (string?)value.AsValue();
        }

        if (propertyType == typeof(int) || propertyType == typeof(int?))
        {
            return (int?)value.AsValue();
        }

        if (propertyType == typeof(long) || propertyType == typeof(long?))
        {
            return (long?)value.AsValue();
        }

        if (propertyType == typeof(float) || propertyType == typeof(float?))
        {
            return (float?)value.AsValue();
        }

        if (propertyType == typeof(double) || propertyType == typeof(double?))
        {
            return (double?)value.AsValue();
        }

        if (propertyType == typeof(bool) || propertyType == typeof(bool?))
        {
            return (bool?)value.AsValue();
        }

        if (propertyType == typeof(DateTimeOffset) || propertyType == typeof(DateTimeOffset?))
        {
            return value.GetValue<DateTimeOffset>();
        }

        if (typeof(IEnumerable).IsAssignableFrom(propertyType))
        {
            return value.Deserialize(propertyType);
        }

        return null;
    }
}
