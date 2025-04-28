// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using MEAI = Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Class for mapping between a json node stored in Azure CosmosDB NoSQL and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class AzureCosmosDBNoSQLVectorStoreRecordMapper<TRecord>(VectorStoreRecordModel model, JsonSerializerOptions? jsonSerializerOptions)
    : ICosmosNoSQLMapper<TRecord>
{
    private readonly VectorStoreRecordKeyPropertyModel _keyProperty = model.KeyProperty;

    public JsonObject MapFromDataToStorageModel(TRecord dataModel, MEAI.Embedding?[]? generatedEmbeddings)
    {
        var jsonObject = JsonSerializer.SerializeToNode(dataModel, jsonSerializerOptions)!.AsObject();

        // The key property in Azure CosmosDB NoSQL is always named 'id'.
        // But the external JSON serializer used just above isn't aware of that, and will produce a JSON object with another name, taking into
        // account e.g. naming policies. TemporaryStorageName gets populated in the model builder - containing that name - once VectorStoreModelBuildingOptions.ReservedKeyPropertyName is set
        RenameJsonProperty(jsonObject, this._keyProperty.TemporaryStorageName!, AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName);

        // Go over the vector properties; those which have an embedding generator configured on them will have embedding generators, overwrite
        // the value in the JSON object with that.
        if (generatedEmbeddings is not null)
        {
            for (var i = 0; i < model.VectorProperties.Count; i++)
            {
                if (generatedEmbeddings[i] is not null)
                {
                    var property = model.VectorProperties[i];
                    Debug.Assert(property.EmbeddingGenerator is not null);
                    var embedding = generatedEmbeddings[i];
                    jsonObject[property.StorageName] = embedding switch
                    {
                        Embedding<float> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        Embedding<byte> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        Embedding<sbyte> e => JsonSerializer.SerializeToNode(e.Vector, jsonSerializerOptions),
                        _ => throw new UnreachableException()
                    };
                }
            }
        }

        return jsonObject;
    }

    public TRecord MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        // See above comment.
        RenameJsonProperty(storageModel, AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName, this._keyProperty.TemporaryStorageName!);

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
