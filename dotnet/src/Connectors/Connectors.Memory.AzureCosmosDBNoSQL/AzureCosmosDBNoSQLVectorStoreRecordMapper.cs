// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Class for mapping between a json node stored in Azure CosmosDB NoSQL and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class AzureCosmosDBNoSQLVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, JsonObject>
{
    /// <summary>The JSON serializer options to use when converting between the data model and the Azure CosmosDB NoSQL record.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>The storage property name of the key field of consumer data model.</summary>
    private readonly string _keyStoragePropertyName;

    /// <summary>A dictionary that maps from a property name to the storage name that should be used when serializing it to json for data and vector properties.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames = [];

    public AzureCosmosDBNoSQLVectorStoreRecordMapper(
        string keyStoragePropertyName,
        Dictionary<string, string> storagePropertyNames,
        JsonSerializerOptions jsonSerializerOptions)
    {
        Verify.NotNull(jsonSerializerOptions);

        this._keyStoragePropertyName = keyStoragePropertyName;
        this._storagePropertyNames = storagePropertyNames;
        this._jsonSerializerOptions = jsonSerializerOptions;
    }

    public JsonObject MapFromDataToStorageModel(TRecord dataModel)
    {
        var jsonObject = JsonSerializer.SerializeToNode(dataModel, this._jsonSerializerOptions)!.AsObject();

        // Key property in Azure CosmosDB NoSQL has a reserved name.
        RenameJsonProperty(jsonObject, this._keyStoragePropertyName, AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName);

        return jsonObject;
    }

    public TRecord MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        // Rename key property for valid deserialization.
        RenameJsonProperty(storageModel, AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName, this._keyStoragePropertyName);

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
