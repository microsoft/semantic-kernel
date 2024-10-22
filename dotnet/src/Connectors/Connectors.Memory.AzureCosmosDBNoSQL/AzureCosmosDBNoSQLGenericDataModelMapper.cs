// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Azure CosmosDB NoSQL.
/// </summary>
internal sealed class AzureCosmosDBNoSQLGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, JsonObject>
{
    /// <summary>A default <see cref="JsonSerializerOptions"/> for serialization/deserialization of vector properties.</summary>
    private static readonly JsonSerializerOptions s_vectorJsonSerializerOptions = new()
    {
        Converters = { new AzureCosmosDBNoSQLReadOnlyMemoryByteConverter() }
    };

    /// <summary>A <see cref="JsonSerializerOptions"/> for serialization/deserialization of data properties</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>The list of properties from the record definition.</summary>
    private readonly IReadOnlyList<VectorStoreRecordProperty> _properties;

    /// <summary>A dictionary that maps from a property name to the storage name.</summary>
    public readonly Dictionary<string, string> _storagePropertyNames;

    public AzureCosmosDBNoSQLGenericDataModelMapper(
        IReadOnlyList<VectorStoreRecordProperty> properties,
        Dictionary<string, string> storagePropertyNames,
        JsonSerializerOptions jsonSerializerOptions)
    {
        Verify.NotNull(properties);

        this._properties = properties;
        this._storagePropertyNames = storagePropertyNames;
        this._jsonSerializerOptions = jsonSerializerOptions;
    }

    public JsonObject MapFromDataToStorageModel(VectorStoreGenericDataModel<string> dataModel)
    {
        Verify.NotNull(dataModel);

        var jsonObject = new JsonObject();

        // Loop through all known properties and map each from the data model to the storage model.
        foreach (var property in this._properties)
        {
            var storagePropertyName = this._storagePropertyNames[property.DataModelPropertyName];

            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                jsonObject[AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName] = dataModel.Key;
            }
            else if (property is VectorStoreRecordDataProperty dataProperty)
            {
                if (dataModel.Data is not null && dataModel.Data.TryGetValue(dataProperty.DataModelPropertyName, out var dataValue))
                {
                    jsonObject[storagePropertyName] = dataValue is not null ?
                        JsonSerializer.SerializeToNode(dataValue, property.PropertyType, this._jsonSerializerOptions) :
                        null;
                }
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                if (dataModel.Vectors is not null && dataModel.Vectors.TryGetValue(vectorProperty.DataModelPropertyName, out var vectorValue))
                {
                    jsonObject[storagePropertyName] = vectorValue is not null ?
                        JsonSerializer.SerializeToNode(vectorValue, property.PropertyType, s_vectorJsonSerializerOptions) :
                        null;
                }
            }
        }

        return jsonObject;
    }

    public VectorStoreGenericDataModel<string> MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        // Create variables to store the response properties.
        string? key = null;
        var dataProperties = new Dictionary<string, object?>();
        var vectorProperties = new Dictionary<string, object?>();

        // Loop through all known properties and map each from the storage model to the data model.
        foreach (var property in this._properties)
        {
            var storagePropertyName = this._storagePropertyNames[property.DataModelPropertyName];

            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                if (storageModel.TryGetPropertyValue(AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName, out var keyValue))
                {
                    key = keyValue?.GetValue<string>();
                }
            }
            else if (property is VectorStoreRecordDataProperty dataProperty)
            {
                if (storageModel.TryGetPropertyValue(storagePropertyName, out var dataValue))
                {
                    dataProperties.Add(property.DataModelPropertyName, dataValue.Deserialize(property.PropertyType, this._jsonSerializerOptions));
                }
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty && options.IncludeVectors)
            {
                if (storageModel.TryGetPropertyValue(storagePropertyName, out var vectorValue))
                {
                    vectorProperties.Add(property.DataModelPropertyName, vectorValue.Deserialize(property.PropertyType, s_vectorJsonSerializerOptions));
                }
            }
        }

        if (key is null)
        {
            throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
        }

        return new VectorStoreGenericDataModel<string>(key) { Data = dataProperties, Vectors = vectorProperties };
    }
}
