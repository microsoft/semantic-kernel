// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Redis when using JSON.
/// </summary>
internal class RedisJsonDynamicDataModelMapper(VectorStoreRecordModel model, JsonSerializerOptions jsonSerializerOptions) : IRedisJsonMapper<Dictionary<string, object?>>
{
    /// <inheritdoc />
    public (string Key, JsonNode Node) MapFromDataToStorageModel(Dictionary<string, object?> dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        var jsonObject = new JsonObject();

        // Key handled below, outside of the JsonNode

        foreach (var dataProperty in model.DataProperties)
        {
            if (dataModel.TryGetValue(dataProperty.ModelName, out var sourceValue))
            {
                jsonObject.Add(dataProperty.StorageName, sourceValue is null
                    ? null
                    : JsonSerializer.SerializeToNode(sourceValue, dataProperty.Type, jsonSerializerOptions));
            }
        }

        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            if (generatedEmbeddings?[i] is IReadOnlyList<Embedding> propertyEmbedding)
            {
                Debug.Assert(property.EmbeddingGenerator is not null);

                jsonObject.Add(
                    property.StorageName,
                    propertyEmbedding[recordIndex] switch
                    {
                        Embedding<float> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        Embedding<double> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        _ => throw new UnreachableException()
                    });
            }
            else
            {
                // No generated embedding, read the vector directly from the data model
                if (dataModel.TryGetValue(property.ModelName, out var sourceValue))
                {
                    jsonObject.Add(property.StorageName, sourceValue is null
                        ? null
                        : JsonSerializer.SerializeToNode(sourceValue, property.Type, jsonSerializerOptions));
                }
            }
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

        // The key was handled above

        foreach (var dataProperty in model.DataProperties)
        {
            // Replicate null if the property exists but is null.
            if (jsonObject.TryGetPropertyValue(dataProperty.StorageName, out var sourceValue))
            {
                dataModel.Add(dataProperty.ModelName, sourceValue is null
                   ? null
                   : JsonSerializer.Deserialize(sourceValue, dataProperty.Type, jsonSerializerOptions));
            }
        }

        foreach (var vectorProperty in model.VectorProperties)
        {
            // For vector properties which have embedding generation configured, we need to remove the embeddings before deserializing
            // (we can't go back from an embedding to e.g. string).
            // For other cases (no embedding generation), we leave the properties even if IncludeVectors is false.
            if (vectorProperty.EmbeddingGenerator is not null)
            {
                continue;
            }

            // Replicate null if the property exists but is null.
            if (jsonObject.TryGetPropertyValue(vectorProperty.StorageName, out var sourceValue))
            {
                dataModel.Add(vectorProperty.ModelName, sourceValue is null
                   ? null
                   : JsonSerializer.Deserialize(sourceValue, vectorProperty.Type, jsonSerializerOptions));
            }
        }

        return dataModel;
    }
}
