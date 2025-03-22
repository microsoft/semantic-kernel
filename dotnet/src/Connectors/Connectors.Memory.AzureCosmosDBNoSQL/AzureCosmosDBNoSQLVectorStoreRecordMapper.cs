// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Class for mapping between a json node stored in Azure CosmosDB NoSQL and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class AzureCosmosDBNoSQLVectorStoreRecordMapper<TRecord>(VectorStoreRecordKeyPropertyModel keyProperty, JsonSerializerOptions? jsonSerializerOptions)
    : IVectorStoreRecordMapper<TRecord, JsonObject>
{
    private readonly VectorStoreRecordKeyPropertyModel _keyProperty = keyProperty;

    public JsonObject MapFromDataToStorageModel(TRecord dataModel)
    {
        var jsonObject = JsonSerializer.SerializeToNode(dataModel, jsonSerializerOptions)!.AsObject();

        // The key property in Azure CosmosDB NoSQL is always named 'id'.
        // But the external JSON serializer used just above isn't aware of that, and will produce a JSON object with another name, taking into
        // account e.g. naming policies. TemporaryStorageName gets populated in the model builder - containing that name - once VectorStoreModelBuildingOptions.ReservedKeyPropertyName is set
        RenameJsonProperty(jsonObject, this._keyProperty.TemporaryStorageName!, AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName);

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
