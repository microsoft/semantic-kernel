// Copyright (c) Microsoft. All rights reserved.

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
internal sealed class AzureCosmosDBNoSQLGenericDataModelMapper(VectorStoreRecordModel model, JsonSerializerOptions jsonSerializerOptions)
    : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, JsonObject>
{
    /// <summary>A default <see cref="JsonSerializerOptions"/> for serialization/deserialization of vector properties.</summary>
    private static readonly JsonSerializerOptions s_vectorJsonSerializerOptions = new()
    {
        Converters = { new AzureCosmosDBNoSQLReadOnlyMemoryByteConverter() }
    };

    public JsonObject MapFromDataToStorageModel(VectorStoreGenericDataModel<string> dataModel)
    {
        Verify.NotNull(dataModel);

        var jsonObject = new JsonObject();

        // Loop through all known properties and map each from the data model to the storage model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    jsonObject[AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName] = dataModel.Key;
                    break;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    if (dataModel.Data is not null && dataModel.Data.TryGetValue(dataProperty.StorageName, out var dataValue))
                    {
                        jsonObject[dataProperty.StorageName] = dataValue is not null ?
                            JsonSerializer.SerializeToNode(dataValue, property.Type, jsonSerializerOptions) :
                            null;
                    }
                    break;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    if (dataModel.Vectors is not null && dataModel.Vectors.TryGetValue(vectorProperty.StorageName, out var vectorValue))
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

    public VectorStoreGenericDataModel<string> MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        // Create variables to store the response properties.
        string? key = null;
        var dataProperties = new Dictionary<string, object?>();
        var vectorProperties = new Dictionary<string, object?>();

        // Loop through all known properties and map each from the storage model to the data model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    if (storageModel.TryGetPropertyValue(AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName, out var keyValue))
                    {
                        key = keyValue?.GetValue<string>();
                    }
                    break;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    if (storageModel.TryGetPropertyValue(dataProperty.StorageName, out var dataValue))
                    {
                        dataProperties.Add(property.ModelName, dataValue.Deserialize(property.Type, jsonSerializerOptions));
                    }
                    break;

                case VectorStoreRecordVectorPropertyModel vectorProperty when options.IncludeVectors:
                    if (options.IncludeVectors && storageModel.TryGetPropertyValue(vectorProperty.StorageName, out var vectorValue))
                    {
                        vectorProperties.Add(property.ModelName, vectorValue.Deserialize(property.Type, s_vectorJsonSerializerOptions));
                    }
                    break;

                default:
                    throw new UnreachableException();
            }
        }

        if (key is null)
        {
            throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
        }

        return new VectorStoreGenericDataModel<string>(key) { Data = dataProperties, Vectors = vectorProperties };
    }
}
