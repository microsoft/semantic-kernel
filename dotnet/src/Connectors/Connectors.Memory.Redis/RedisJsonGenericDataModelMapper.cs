// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Redis when using JSON.
/// </summary>
internal sealed class RedisJsonGenericDataModelMapper(
    IReadOnlyList<VectorStoreRecordPropertyModel> properties,
    JsonSerializerOptions jsonSerializerOptions)
    : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, (string Key, JsonNode Node)>
{
    /// <inheritdoc />
    public (string Key, JsonNode Node) MapFromDataToStorageModel(VectorStoreGenericDataModel<string> dataModel)
    {
        var jsonObject = new JsonObject();

        foreach (var property in properties)
        {
            var sourceDictionary = property is VectorStoreRecordDataPropertyModel ? dataModel.Data : dataModel.Vectors;

            // Only map properties across that actually exist in the input.
            if (sourceDictionary is null || !sourceDictionary.TryGetValue(property.ModelName, out var sourceValue))
            {
                continue;
            }

            // Replicate null if the property exists but is null.
            if (sourceValue is null)
            {
                jsonObject.Add(property.StorageName, null);
                continue;
            }

            jsonObject.Add(property.StorageName, JsonSerializer.SerializeToNode(sourceValue, property.Type, jsonSerializerOptions));
        }

        return (dataModel.Key, jsonObject);
    }

    /// <inheritdoc />
    public VectorStoreGenericDataModel<string> MapFromStorageToDataModel((string Key, JsonNode Node) storageModel, StorageToDataModelMapperOptions options)
    {
        var dataModel = new VectorStoreGenericDataModel<string>(storageModel.Key);

        // The redis result can be either a single object or an array with a single object in the case where we are doing an MGET.
        var jsonObject = storageModel.Node switch
        {
            JsonObject topLevelJsonObject => topLevelJsonObject,
            JsonArray jsonArray and [JsonObject arrayEntryJsonObject] => arrayEntryJsonObject,
            _ => throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'"),
        };

        foreach (var property in properties)
        {
            var targetDictionary = property is VectorStoreRecordDataPropertyModel ? dataModel.Data : dataModel.Vectors;

            // Only map properties across that actually exist in the input.
            if (!jsonObject.TryGetPropertyValue(property.StorageName, out var sourceValue))
            {
                continue;
            }

            // Replicate null if the property exists but is null.
            if (sourceValue is null)
            {
                targetDictionary.Add(property.ModelName, null);
                continue;
            }

            // Map data and vector values.
            if (property is VectorStoreRecordDataPropertyModel or VectorStoreRecordVectorPropertyModel)
            {
                targetDictionary.Add(property.ModelName, JsonSerializer.Deserialize(sourceValue, property.Type, jsonSerializerOptions));
            }
        }

        return dataModel;
    }
}
