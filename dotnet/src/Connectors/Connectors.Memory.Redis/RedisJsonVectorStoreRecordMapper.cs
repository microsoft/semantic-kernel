// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for mapping between a json node stored in redis, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
internal sealed class RedisJsonVectorStoreRecordMapper<TConsumerDataModel>(
    VectorStoreRecordKeyPropertyModel keyProperty,
    JsonSerializerOptions jsonSerializerOptions)
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    : IVectorStoreRecordMapper<TConsumerDataModel, (string Key, JsonNode Node)>
#pragma warning restore CS0618
{
    /// <summary>The key property.</summary>
    private readonly string _keyPropertyStorageName = keyProperty.StorageName;

    /// <inheritdoc />
    public (string Key, JsonNode Node) MapFromDataToStorageModel(TConsumerDataModel dataModel)
    {
        // Convert the provided record into a JsonNode object and try to get the key field for it.
        // Since we already checked that the key field is a string in the constructor, and that it exists on the model,
        // the only edge case we have to be concerned about is if the key field is null.
        var jsonNode = JsonSerializer.SerializeToNode(dataModel, jsonSerializerOptions);
        if (jsonNode!.AsObject().TryGetPropertyValue(this._keyPropertyStorageName, out var keyField) && keyField is JsonValue jsonValue)
        {
            // Remove the key field from the JSON object since we don't want to store it in the redis payload.
            var keyValue = jsonValue.ToString();
            jsonNode.AsObject().Remove(this._keyPropertyStorageName);

            return (keyValue, jsonNode);
        }

        throw new VectorStoreRecordMappingException($"Missing key field {this._keyPropertyStorageName} on provided record of type {typeof(TConsumerDataModel).FullName}.");
    }

    /// <inheritdoc />
    public TConsumerDataModel MapFromStorageToDataModel((string Key, JsonNode Node) storageModel, StorageToDataModelMapperOptions options)
    {
        // The redis result can be either a single object or an array with a single object in the case where we are doing an MGET.
        var jsonObject = storageModel.Node switch
        {
            JsonObject topLevelJsonObject => topLevelJsonObject,
            JsonArray and [JsonObject arrayEntryJsonObject] => arrayEntryJsonObject,
            _ => throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'")
        };

        // Check that the key field is not already present in the redis value.
        if (jsonObject.ContainsKey(this._keyPropertyStorageName))
        {
            throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'. Key property '{this._keyPropertyStorageName}' is already present on retrieved object.");
        }

        // Since the key is not stored in the redis value, add it back in before deserializing into the data model.
        jsonObject.Add(this._keyPropertyStorageName, storageModel.Key);

        return JsonSerializer.Deserialize<TConsumerDataModel>(jsonObject, jsonSerializerOptions)!;
    }
}
