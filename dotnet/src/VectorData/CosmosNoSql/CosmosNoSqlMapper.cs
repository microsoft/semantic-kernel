// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;
using MEAI = Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

/// <summary>
/// Class for mapping between a json node stored in Azure CosmosDB NoSQL and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class CosmosNoSqlMapper<TRecord>(CollectionModel model, JsonSerializerOptions? jsonSerializerOptions)
    : ICosmosNoSqlMapper<TRecord>
    where TRecord : class
{
    private readonly KeyPropertyModel _keyProperty = model.KeyProperty;

    public JsonObject MapFromDataToStorageModel(TRecord dataModel, int recordIndex, IReadOnlyList<MEAI.Embedding>?[]? generatedEmbeddings)
    {
        var jsonObject = JsonSerializer.SerializeToNode(dataModel, jsonSerializerOptions)!.AsObject();

        // The key property in Azure CosmosDB NoSQL is always named 'id'.
        // But the external JSON serializer used just above isn't aware of that, and will produce a JSON object with another name, taking into
        // account e.g. naming policies. TemporaryStorageName gets populated in the model builder - containing that name - once VectorStoreModelBuildingOptions.ReservedKeyPropertyName is set
        RenameJsonProperty(jsonObject, this._keyProperty.TemporaryStorageName!, CosmosNoSqlConstants.ReservedKeyPropertyName);

        // Go over the vector properties; inject any generated embeddings to overwrite the JSON serialized above.
        // Also, for Embedding<T> properties we also need to overwrite with a simple array (since Embedding<T> gets serialized as a complex object).
        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            Embedding? embedding = generatedEmbeddings?[i]?[recordIndex] is Embedding ge ? ge : null;

            if (embedding is null)
            {
                switch (Nullable.GetUnderlyingType(property.Type) ?? property.Type)
                {
                    case var t when t == typeof(ReadOnlyMemory<float>):
                    case var t2 when t2 == typeof(float[]):
                        // The .NET vector property is a ReadOnlyMemory<float> or float[] (not an Embedding), which means that JsonSerializer
                        // already serialized it correctly above.
                        // In addition, there's no generated embedding (which would be an Embedding which we'd need to handle manually).
                        // So there's nothing for us to do.
                        continue;

                    // byte/sbyte is a special case, since it gets serialized as base64 by default; handle manually here.
                    case var t3 when t3 == typeof(ReadOnlyMemory<byte>):
                        embedding = new Embedding<byte>((ReadOnlyMemory<byte>)property.GetValueAsObject(dataModel)!);
                        break;
                    case var t4 when t4 == typeof(byte[]):
                        embedding = new Embedding<byte>((byte[])property.GetValueAsObject(dataModel)!);
                        break;
                    case var t5 when t5 == typeof(ReadOnlyMemory<sbyte>):
                        embedding = new Embedding<sbyte>((ReadOnlyMemory<sbyte>)property.GetValueAsObject(dataModel)!);
                        break;
                    case var t6 when t6 == typeof(sbyte[]):
                        embedding = new Embedding<sbyte>((sbyte[])property.GetValueAsObject(dataModel)!);
                        break;

                    case var t when t == typeof(Embedding<float>):
                    case var t1 when t1 == typeof(Embedding<byte>):
                    case var t2 when t2 == typeof(Embedding<sbyte>):
                        embedding = (Embedding)property.GetValueAsObject(dataModel)!;
                        break;

                    default:
                        throw new UnreachableException();
                }
            }

            var jsonArray = new JsonArray();

            switch (embedding)
            {
                case Embedding<float> e:
                    foreach (var item in e.Vector.Span)
                    {
                        jsonArray.Add(JsonValue.Create(item));
                    }
                    break;

                case Embedding<byte> e:
                    foreach (var item in e.Vector.Span)
                    {
                        jsonArray.Add(JsonValue.Create(item));
                    }
                    break;

                case Embedding<sbyte> e:
                    foreach (var item in e.Vector.Span)
                    {
                        jsonArray.Add(JsonValue.Create(item));
                    }
                    break;

                default:
                    throw new UnreachableException();
            }

            jsonObject[property.StorageName] = jsonArray;
        }

        return jsonObject;
    }

    public TRecord MapFromStorageToDataModel(JsonObject storageModel, bool includeVectors)
    {
        // See above comment.
        RenameJsonProperty(storageModel, CosmosNoSqlConstants.ReservedKeyPropertyName, this._keyProperty.TemporaryStorageName!);

        if (includeVectors)
        {
            foreach (var vectorProperty in model.VectorProperties)
            {
                if (vectorProperty.Type == typeof(Embedding<float>))
                {
                    var arrayNode = storageModel[vectorProperty.StorageName];
                    if (arrayNode is not null)
                    {
                        var embeddingNode = new JsonObject();
                        embeddingNode[nameof(Embedding<float>.Vector)] = arrayNode.DeepClone();
                        storageModel[vectorProperty.StorageName] = embeddingNode;
                    }
                }
            }
        }

        return storageModel.Deserialize<TRecord>(jsonSerializerOptions)!;
    }

    #region private

    private static void RenameJsonProperty(JsonObject jsonObject, string oldKey, string newKey)
    {
        if (jsonObject is not null && jsonObject.ContainsKey(oldKey))
        {
            JsonNode? value = jsonObject[oldKey];

            jsonObject.Remove(oldKey);

            jsonObject[newKey] = value;
        }
    }

    #endregion
}
