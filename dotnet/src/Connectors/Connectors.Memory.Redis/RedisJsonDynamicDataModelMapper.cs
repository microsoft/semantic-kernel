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
internal class RedisJsonDynamicDataModelMapper(VectorStoreRecordModel model, JsonSerializerOptions jsonSerializerOptions)
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    : IVectorStoreRecordMapper<Dictionary<string, object?>, (string Key, JsonNode Node)>
#pragma warning restore CS0618
{
    /// <inheritdoc />
    public (string Key, JsonNode Node) MapFromDataToStorageModel(Dictionary<string, object?> dataModel)
    {
        var jsonObject = new JsonObject();

        foreach (var property in model.Properties)
        {
            // Key handled below, outside of the JsonNode
            if (property is VectorStoreRecordKeyPropertyModel)
            {
                continue;
            }

            // Only map properties across that actually exist in the input.
            if (!dataModel.TryGetValue(property.ModelName, out var sourceValue))
            {
                continue;
            }

            // Replicate null if the property exists but is null.
            jsonObject.Add(property.StorageName, sourceValue is null
                ? null
                : JsonSerializer.SerializeToNode(sourceValue, property.Type, jsonSerializerOptions));
        }

        return ((string)dataModel[model.KeyProperty.ModelName]!, jsonObject);
    }

    /// <inheritdoc />
    public Dictionary<string, object?> MapFromStorageToDataModel((string Key, JsonNode Node) storageModel, StorageToDataModelMapperOptions options)
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
            _ => throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'"),
        };

        foreach (var property in model.Properties)
        {
            // Key handled above
            if (property is VectorStoreRecordKeyPropertyModel)
            {
                continue;
            }

            // Replicate null if the property exists but is null.
            if (!jsonObject.TryGetPropertyValue(property.StorageName, out var sourceValue))
            {
                continue;
            }

            dataModel.Add(property.ModelName, sourceValue is null
               ? null
               : JsonSerializer.Deserialize(sourceValue, property.Type, jsonSerializerOptions));
        }

        return dataModel;
    }
}
