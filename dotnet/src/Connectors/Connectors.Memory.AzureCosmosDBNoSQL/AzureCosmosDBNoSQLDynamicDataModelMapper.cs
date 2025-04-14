// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Azure CosmosDB NoSQL.
/// </summary>
internal sealed class AzureCosmosDBNoSQLDynamicDataModelMapper(VectorStoreRecordModel model, JsonSerializerOptions jsonSerializerOptions)
    : ICosmosNoSQLMapper<Dictionary<string, object?>>
{
    /// <summary>A default <see cref="JsonSerializerOptions"/> for serialization/deserialization of vector properties.</summary>
    private static readonly JsonSerializerOptions s_vectorJsonSerializerOptions = new()
    {
        Converters = { new AzureCosmosDBNoSQLReadOnlyMemoryByteConverter() }
    };

    public JsonObject MapFromDataToStorageModel(Dictionary<string, object?> dataModel)
    {
        Verify.NotNull(dataModel);

        var jsonObject = new JsonObject();

        // Loop through all known properties and map each from the data model to the storage model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    jsonObject[AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName] = (string)(dataModel[keyProperty.ModelName]
                        ?? throw new InvalidOperationException($"Key property '{keyProperty.ModelName}' is null."));

                    break;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    if (dataModel.TryGetValue(dataProperty.StorageName, out var dataValue))
                    {
                        jsonObject[dataProperty.StorageName] = dataValue is not null ?
                            JsonSerializer.SerializeToNode(dataValue, property.Type, jsonSerializerOptions) :
                            null;
                    }
                    break;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    if (dataModel.TryGetValue(vectorProperty.StorageName, out var vectorValue))
                    {
                        jsonObject[vectorProperty.StorageName] = vectorValue is not null ?
                            JsonSerializer.SerializeToNode(vectorValue, property.Type, s_vectorJsonSerializerOptions) :
                            null;
                    }
                    break;

                default:
                    throw new UnreachableException();
            }
        }

        return jsonObject;
    }

    public Dictionary<string, object?> MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        var result = new Dictionary<string, object?>();

        // Loop through all known properties and map each from the storage model to the data model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    result[keyProperty.ModelName] = storageModel.TryGetPropertyValue(AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName, out var keyValue)
                        ? keyValue?.GetValue<string>()
                        : throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
                    continue;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    if (storageModel.TryGetPropertyValue(dataProperty.StorageName, out var dataValue))
                    {
                        result.Add(property.ModelName, dataValue.Deserialize(property.Type, jsonSerializerOptions));
                    }
                    continue;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    if (options.IncludeVectors && storageModel.TryGetPropertyValue(vectorProperty.StorageName, out var vectorValue))
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
