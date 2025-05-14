// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for mapping between a json node stored in redis, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
internal sealed class RedisJsonVectorStoreRecordMapper<TConsumerDataModel>(
    VectorStoreRecordModel model,
    JsonSerializerOptions jsonSerializerOptions)
    : IRedisJsonMapper<TConsumerDataModel>
{
    /// <summary>The key property.</summary>
    private readonly string _keyPropertyStorageName = model.KeyProperty.StorageName;

    /// <inheritdoc />
    public (string Key, JsonNode Node) MapFromDataToStorageModel(TConsumerDataModel dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        // Convert the provided record into a JsonNode object and try to get the key field for it.
        // Since we already checked that the key field is a string in the constructor, and that it exists on the model,
        // the only edge case we have to be concerned about is if the key field is null.
        var jsonNode = JsonSerializer.SerializeToNode(dataModel, jsonSerializerOptions)!.AsObject();

        if (!(jsonNode.TryGetPropertyValue(this._keyPropertyStorageName, out var keyField) && keyField is JsonValue jsonValue))
        {
            throw new VectorStoreRecordMappingException($"Missing key field '{this._keyPropertyStorageName}' on provided record of type {typeof(TConsumerDataModel).FullName}.");
        }

        // Remove the key field from the JSON object since we don't want to store it in the redis payload.
        var keyValue = jsonValue.ToString();
        jsonNode.Remove(this._keyPropertyStorageName);

        // Go over the vector properties; those which have an embedding generator configured on them will have embedding generators, overwrite
        // the value in the JSON object with that.
        if (generatedEmbeddings is not null)
        {
            for (var i = 0; i < model.VectorProperties.Count; i++)
            {
                if (generatedEmbeddings[i] is IReadOnlyList<Embedding> propertyEmbeddings)
                {
                    var property = model.VectorProperties[i];
                    Debug.Assert(property.EmbeddingGenerator is not null);
                    jsonNode[property.StorageName] = propertyEmbeddings[recordIndex] switch
                    {
                        Embedding<float> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        Embedding<double> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        _ => throw new UnreachableException()
                    };
                }
            }
        }

        return (keyValue, jsonNode);
    }

    /// <inheritdoc />
    public TConsumerDataModel MapFromStorageToDataModel((string Key, JsonNode Node) storageModel, StorageToDataModelMapperOptions options)
    {
        // The redis result can have one of three different formats:
        // 1. a single object
        // 2. an array with a single object in the case where we are doing an MGET
        // 3. a single value (string, number, etc.) in the case where there is only one property being requested because the model has only one property apart from the key
        var jsonObject = storageModel.Node switch
        {
            JsonObject topLevelJsonObject => topLevelJsonObject,
            JsonArray and [JsonObject arrayEntryJsonObject] => arrayEntryJsonObject,
            JsonValue when model.DataProperties.Count + model.VectorProperties.Count == 1 => new JsonObject
            {
                [model.DataProperties.Concat<VectorStoreRecordPropertyModel>(model.VectorProperties).First().StorageName] = storageModel.Node
            },
            _ => throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'")
        };

        // Check that the key field is not already present in the redis value.
        if (jsonObject.ContainsKey(this._keyPropertyStorageName))
        {
            throw new VectorStoreRecordMappingException($"Invalid data format for document with key '{storageModel.Key}'. Key property '{this._keyPropertyStorageName}' is already present on retrieved object.");
        }

        // Since the key is not stored in the redis value, add it back in before deserializing into the data model.
        jsonObject.Add(this._keyPropertyStorageName, storageModel.Key);

        // For vector properties which have embedding generation configured, we need to remove the embeddings before deserializing
        // (we can't go back from an embedding to e.g. string).
        // For other cases (no embedding generation), we leave the properties even if IncludeVectors is false.
        if (!options.IncludeVectors)
        {
            foreach (var vectorProperty in model.VectorProperties)
            {
                if (vectorProperty.EmbeddingGenerator is not null)
                {
                    jsonObject.Remove(vectorProperty.StorageName);
                }
            }
        }

        return JsonSerializer.Deserialize<TConsumerDataModel>(jsonObject, jsonSerializerOptions)!;
    }
}
