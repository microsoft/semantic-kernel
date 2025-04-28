// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Azure AI Search.
/// </summary>
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
internal sealed class AzureAISearchDynamicDataModelMapper(VectorStoreRecordModel model)
#pragma warning restore CS0618
{
    /// <inheritdoc />
    public JsonObject MapFromDataToStorageModel(Dictionary<string, object?> dataModel)
    {
        Verify.NotNull(dataModel);

        var storageJsonObject = new JsonObject();

        // Loop through all known properties and map each from the data model json to the storage json.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    storageJsonObject.Add(keyProperty.StorageName, (string)model.KeyProperty.GetValueAsObject(dataModel)!);
                    continue;

                case VectorStoreRecordDataPropertyModel dataProperty:
                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    if (dataModel.TryGetValue(property.ModelName, out var dataValue))
                    {
                        var serializedJsonNode = JsonSerializer.SerializeToNode(dataValue);
                        storageJsonObject.Add(property.StorageName, serializedJsonNode);
                    }
                    continue;

                default:
                    throw new UnreachableException();
            }
        }

        return storageJsonObject;
    }

    /// <inheritdoc />
    public Dictionary<string, object?> MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        // Create variables to store the response properties.
        var result = new Dictionary<string, object?>();

        // Loop through all known properties and map each from json to the data type.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    result[keyProperty.ModelName] = (string?)storageModel[keyProperty.StorageName]
                        ?? throw new VectorStoreRecordMappingException($"The key property '{keyProperty.StorageName}' is missing from the record retrieved from storage.");

                    continue;

                case VectorStoreRecordDataPropertyModel dataProperty:
                {
                    if (storageModel.TryGetPropertyValue(dataProperty.StorageName, out var value))
                    {
                        result.Add(dataProperty.ModelName, value is null ? null : GetDataPropertyValue(property.Type, value));
                    }
                    continue;
                }

                case VectorStoreRecordVectorPropertyModel vectorProperty when options.IncludeVectors:
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

                case VectorStoreRecordVectorPropertyModel vectorProperty when !options.IncludeVectors:
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
