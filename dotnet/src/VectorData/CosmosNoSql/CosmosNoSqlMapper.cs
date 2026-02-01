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
internal sealed class CosmosNoSqlMapper<TRecord> : ICosmosNoSqlMapper<TRecord>
    where TRecord : class
{
    private readonly CollectionModel _model;
    private readonly KeyPropertyModel _keyProperty;
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    public CosmosNoSqlMapper(CollectionModel model, JsonSerializerOptions? jsonSerializerOptions)
    {
        this._model = model;
        this._keyProperty = model.KeyProperty;

        // Add byte array converters to serialize byte[] and ReadOnlyMemory<byte> as JSON arrays of numbers
        // instead of base64-encoded strings, which is required for Cosmos DB vector operations.
        var newOptions = new JsonSerializerOptions(jsonSerializerOptions ?? JsonSerializerOptions.Default);
        newOptions.Converters.Add(new ByteArrayJsonConverter());
        newOptions.Converters.Add(new ReadOnlyMemoryByteJsonConverter());
        this._jsonSerializerOptions = newOptions;
    }

    public JsonObject MapFromDataToStorageModel(TRecord dataModel, int recordIndex, IReadOnlyList<MEAI.Embedding>?[]? generatedEmbeddings)
    {
        var jsonObject = JsonSerializer.SerializeToNode(dataModel, this._jsonSerializerOptions)!.AsObject();

        // The key property in Azure CosmosDB NoSQL is always named 'id'.
        // But the external JSON serializer used just above isn't aware of that, and will produce a JSON object with another name, taking into
        // account e.g. naming policies. TemporaryStorageName gets populated in the model builder - containing that name - once VectorStoreModelBuildingOptions.ReservedKeyPropertyName is set
        RenameJsonProperty(jsonObject, this._keyProperty.TemporaryStorageName!, CosmosNoSqlConstants.ReservedKeyPropertyName);

        // Go over the vector properties; inject any generated embeddings to overwrite the JSON serialized above.
        // Also, for Embedding<T> properties we also need to overwrite with a simple array (since Embedding<T> gets serialized as a complex object).
        for (var i = 0; i < this._model.VectorProperties.Count; i++)
        {
            var property = this._model.VectorProperties[i];

            Embedding? embedding = generatedEmbeddings?[i]?[recordIndex] is Embedding ge ? ge : null;

            if (embedding is null)
            {
                switch (Nullable.GetUnderlyingType(property.Type) ?? property.Type)
                {
                    // For raw array/memory types, JsonSerializer already serialized them correctly above
                    // (including byte[] thanks to our custom converter). Nothing more to do.
                    case var t when t == typeof(ReadOnlyMemory<float>):
                    case var t2 when t2 == typeof(float[]):
                    case var t3 when t3 == typeof(ReadOnlyMemory<byte>):
                    case var t4 when t4 == typeof(byte[]):
                    case var t5 when t5 == typeof(ReadOnlyMemory<sbyte>):
                    case var t6 when t6 == typeof(sbyte[]):
                        continue;

                    // For Embedding<T> types, we need to extract the vector and serialize it as a simple array
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
            foreach (var vectorProperty in this._model.VectorProperties)
            {
                var arrayNode = storageModel[vectorProperty.StorageName];
                if (arrayNode is null)
                {
                    continue;
                }

                // Embedding<T> is stored as a simple JSON array, so convert it to the expected object shape for deserialization
                if (vectorProperty.Type == typeof(Embedding<float>)
                    || vectorProperty.Type == typeof(Embedding<byte>)
                    || vectorProperty.Type == typeof(Embedding<sbyte>))
                {
                    storageModel[vectorProperty.StorageName] = new JsonObject
                    {
                        [nameof(Embedding<>.Vector)] = arrayNode.DeepClone()
                    };
                }

                // For byte[], ReadOnlyMemory<byte>, sbyte[], ReadOnlyMemory<sbyte>, float[], ReadOnlyMemory<float>,
                // the custom converters (for byte) and default converters (for others) handle deserialization correctly.
            }
        }

        return storageModel.Deserialize<TRecord>(this._jsonSerializerOptions)!;
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
