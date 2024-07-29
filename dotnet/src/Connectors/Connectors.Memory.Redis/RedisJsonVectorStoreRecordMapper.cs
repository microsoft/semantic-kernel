// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for mapping between a json node stored in redis, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
internal sealed class RedisJsonVectorStoreRecordMapper<TConsumerDataModel> : IVectorStoreRecordMapper<TConsumerDataModel, (string Key, JsonNode Node)>
    where TConsumerDataModel : class
{
    /// <summary>The name of the temporary json property that the key field will be serialized / parsed from.</summary>
    private readonly string _keyFieldJsonPropertyName;

    /// <summary>The JSON serializer options to use when converting between the data model and the Redis record.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisJsonVectorStoreRecordMapper{TConsumerDataModel}"/> class.
    /// </summary>
    /// <param name="keyFieldJsonPropertyName">The name of the key field on the model when serialized to json.</param>
    /// <param name="jsonSerializerOptions">The JSON serializer options to use when converting between the data model and the Redis record.</param>
    public RedisJsonVectorStoreRecordMapper(string keyFieldJsonPropertyName, JsonSerializerOptions jsonSerializerOptions)
    {
        Verify.NotNullOrWhiteSpace(keyFieldJsonPropertyName);
        Verify.NotNull(jsonSerializerOptions);

        this._keyFieldJsonPropertyName = keyFieldJsonPropertyName;
        this._jsonSerializerOptions = jsonSerializerOptions;
    }

    /// <inheritdoc />
    public (string Key, JsonNode Node) MapFromDataToStorageModel(TConsumerDataModel dataModel)
    {
        // Convert the provided record into a JsonNode object and try to get the key field for it.
        // Since we already checked that the key field is a string in the constructor, and that it exists on the model,
        // the only edge case we have to be concerned about is if the key field is null.
        var jsonNode = JsonSerializer.SerializeToNode(dataModel, this._jsonSerializerOptions);
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

        return JsonSerializer.Deserialize<TConsumerDataModel>(jsonObject, this._jsonSerializerOptions)!;
    }
}
