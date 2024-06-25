// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for mapping between a json node stored in redis, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
internal sealed class RedisVectorStoreRecordMapper<TConsumerDataModel> : IVectorStoreRecordMapper<TConsumerDataModel, (string Key, JsonNode Node)>
    where TConsumerDataModel : class
{
    /// <summary>The name of the temporary json property that the key field will be serialized / parsed from.</summary>
    private readonly string _keyFieldJsonPropertyName;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisVectorStoreRecordMapper{TConsumerDataModel}"/> class.
    /// </summary>
    /// <param name="keyFieldJsonPropertyName">The name of the key field on the model when serialized to json.</param>
    public RedisVectorStoreRecordMapper(string keyFieldJsonPropertyName)
    {
        Verify.NotNullOrWhiteSpace(keyFieldJsonPropertyName);
        this._keyFieldJsonPropertyName = keyFieldJsonPropertyName;
    }

    /// <inheritdoc />
    public (string Key, JsonNode Node) MapFromDataToStorageModel(TConsumerDataModel dataModel)
    {
        // Convert the provided record into a JsonNode object and try to get the key field for it.
        // Since we already checked that the key field is a string in the constructor, and that it exists on the model,
        // the only edge case we have to be concerned about is if the key field is null.
        var jsonNode = JsonSerializer.SerializeToNode(dataModel);
        if (jsonNode!.AsObject().TryGetPropertyValue(this._keyFieldJsonPropertyName, out var keyField) && keyField is JsonValue jsonValue)
        {
            // Remove the key field from the JSON object since we don't want to store it in the redis payload.
            var keyValue = jsonValue.ToString();
            jsonNode.AsObject().Remove(this._keyFieldJsonPropertyName);

            return (keyValue, jsonNode);
        }

        throw new VectorStoreRecordMappingException($"Missing key field {this._keyFieldJsonPropertyName} on provided record of type {typeof(TConsumerDataModel).FullName}.");
    }

    /// <inheritdoc />
    public TConsumerDataModel MapFromStorageToDataModel((string Key, JsonNode Node) storageModel, StorageToDataModelMapperOptions options)
    {
        JsonObject jsonObject;

        // The redis result can be either a single object or an array with a single object in the case where we are doing an MGET.
        if (storageModel.Node is JsonObject topLevelJsonObject)
        {
            jsonObject = topLevelJsonObject;
        }
        else if (storageModel.Node is JsonArray jsonArray && jsonArray.Count == 1 && jsonArray[0] is JsonObject arrayEntryJsonObject)
        {
            jsonObject = arrayEntryJsonObject;
        }
        else
        {
            throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'");
        }

        // Check that the key field is not already present in the redis value.
        if (jsonObject.ContainsKey(this._keyFieldJsonPropertyName))
        {
            throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'. Key property '{this._keyFieldJsonPropertyName}' is already present on retrieved object.");
        }

        // Since the key is not stored in the redis value, add it back in before deserializing into the data model.
        jsonObject.Add(this._keyFieldJsonPropertyName, storageModel.Key);

        return JsonSerializer.Deserialize<TConsumerDataModel>(jsonObject)!;
    }
}
