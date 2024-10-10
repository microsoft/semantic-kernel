// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Azure AI Search.
/// </summary>
internal class AzureAISearchGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, JsonObject>
{
    /// <summary>A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAISearchGenericDataModelMapper"/> class.
    /// </summary>
    /// <param name="vectorStoreRecordDefinition">A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</param>
    public AzureAISearchGenericDataModelMapper(VectorStoreRecordDefinition vectorStoreRecordDefinition)
    {
        Verify.NotNull(vectorStoreRecordDefinition);

        this._vectorStoreRecordDefinition = vectorStoreRecordDefinition;
    }

    /// <inheritdoc />
    public JsonObject MapFromDataToStorageModel(VectorStoreGenericDataModel<string> dataModel)
    {
        Verify.NotNull(dataModel);

        var storageJsonObject = new JsonObject();

        // Loop through all known properties and map each from the data model json to the storage json.
        foreach (var property in this._vectorStoreRecordDefinition.Properties)
        {
            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                var storagePropertyName = keyProperty.StoragePropertyName ?? keyProperty.DataModelPropertyName;
                storageJsonObject.Add(storagePropertyName, dataModel.Key);
            }
            else if (property is VectorStoreRecordDataProperty dataProperty)
            {
                if (dataModel.Data is not null && dataModel.Data.TryGetValue(dataProperty.DataModelPropertyName, out var dataValue))
                {
                    var storagePropertyName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;
                    var serializedJsonNode = JsonSerializer.SerializeToNode(dataValue);
                    storageJsonObject.Add(storagePropertyName, serializedJsonNode);
                }
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                if (dataModel.Vectors is not null && dataModel.Vectors.TryGetValue(vectorProperty.DataModelPropertyName, out var vectorValue))
                {
                    var storagePropertyName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;
                    var serializedJsonNode = JsonSerializer.SerializeToNode(vectorValue);
                    storageJsonObject.Add(storagePropertyName, serializedJsonNode);
                }
            }
        }

        return storageJsonObject;
    }

    /// <inheritdoc />
    public VectorStoreGenericDataModel<string> MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        // Create variables to store the response properties.
        var dataProperties = new Dictionary<string, object?>();
        var vectorProperties = new Dictionary<string, object?>();
        string? key = null;

        // Loop through all known properties and map each from json to the data type.
        foreach (var property in this._vectorStoreRecordDefinition.Properties)
        {
            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                var storagePropertyName = keyProperty.StoragePropertyName ?? keyProperty.DataModelPropertyName;
                var value = storageModel[storagePropertyName];
                if (value is null)
                {
                    throw new VectorStoreRecordMappingException($"The key property '{storagePropertyName}' is missing from the record retrieved from storage.");
                }

                key = (string)value!;
            }
            else if (property is VectorStoreRecordDataProperty dataProperty)
            {
                var storagePropertyName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;
                if (!storageModel.TryGetPropertyValue(storagePropertyName, out var value))
                {
                    continue;
                }

                if (value is not null)
                {
                    dataProperties.Add(dataProperty.DataModelPropertyName, GetDataPropertyValue(property.PropertyType, value));
                }
                else
                {
                    dataProperties.Add(dataProperty.DataModelPropertyName, null);
                }
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty && options.IncludeVectors)
            {
                var storagePropertyName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;
                if (!storageModel.TryGetPropertyValue(storagePropertyName, out var value))
                {
                    continue;
                }

                if (value is not null)
                {
                    ReadOnlyMemory<float> vector = value.AsArray().Select(x => (float)x!).ToArray();
                    vectorProperties.Add(vectorProperty.DataModelPropertyName, vector);
                }
                else
                {
                    vectorProperties.Add(vectorProperty.DataModelPropertyName, null);
                }
            }
        }

        if (key is null)
        {
            throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
        }

        return new VectorStoreGenericDataModel<string>(key) { Data = dataProperties, Vectors = vectorProperties };
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
