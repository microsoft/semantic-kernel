// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
internal sealed class WeaviateVectorStoreRecordMapper<TRecord> : IWeaviateMapper<TRecord>
#pragma warning restore CS0618
{
    private readonly string _collectionName;
    private readonly VectorStoreRecordModel _model;
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    public WeaviateVectorStoreRecordMapper(
        string collectionName,
        VectorStoreRecordModel model,
        JsonSerializerOptions jsonSerializerOptions)
    {
        this._collectionName = collectionName;
        this._model = model;
        this._jsonSerializerOptions = jsonSerializerOptions;
    }

    public JsonObject MapFromDataToStorageModel(TRecord dataModel)
    {
        Verify.NotNull(dataModel);

        var jsonNodeDataModel = JsonSerializer.SerializeToNode(dataModel, this._jsonSerializerOptions)!;

        // Transform data model to Weaviate object model.
        var weaviateObjectModel = new JsonObject
        {
            { WeaviateConstants.CollectionPropertyName, JsonValue.Create(this._collectionName) },
            // The key property in Weaviate is always named 'id'.
            // But the external JSON serializer used just above isn't aware of that, and will produce a JSON object with another name, taking into
            // account e.g. naming policies. TemporaryStorageName gets populated in the model builder - containing that name - once VectorStoreModelBuildingOptions.ReservedKeyPropertyName is set
            { WeaviateConstants.ReservedKeyPropertyName, jsonNodeDataModel[this._model.KeyProperty.TemporaryStorageName!]!.DeepClone() },
            { WeaviateConstants.ReservedDataPropertyName, new JsonObject() },
            { WeaviateConstants.ReservedVectorPropertyName, new JsonObject() },
        };

        // Populate data properties.
        foreach (var property in this._model.DataProperties)
        {
            var node = jsonNodeDataModel[property.StorageName];

            if (node is not null)
            {
                weaviateObjectModel[WeaviateConstants.ReservedDataPropertyName]![property.StorageName] = node.DeepClone();
            }
        }

        // Populate vector properties.
        foreach (var property in this._model.VectorProperties)
        {
            var node = jsonNodeDataModel[property.StorageName];

            if (node is not null)
            {
                weaviateObjectModel[WeaviateConstants.ReservedVectorPropertyName]![property.StorageName] = node.DeepClone();
            }
        }

        return weaviateObjectModel;
    }

    public TRecord MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        // TemporaryStorageName gets populated in the model builder once VectorStoreModelBuildingOptions.ReservedKeyPropertyName is set
        Debug.Assert(this._model.KeyProperty.TemporaryStorageName is not null);

        // Transform Weaviate object model to data model.
        var jsonNodeDataModel = new JsonObject
        {
            // See comment above on TemporaryStorageName
            { this._model.KeyProperty.TemporaryStorageName!, storageModel[WeaviateConstants.ReservedKeyPropertyName]?.DeepClone() },
        };

        // Populate data properties.
        foreach (var property in this._model.DataProperties)
        {
            var node = storageModel[WeaviateConstants.ReservedDataPropertyName]?[property.StorageName];

            if (node is not null)
            {
                jsonNodeDataModel[property.StorageName] = node.DeepClone();
            }
        }

        // Populate vector properties.
        if (options.IncludeVectors)
        {
            foreach (var property in this._model.VectorProperties)
            {
                var node = storageModel[WeaviateConstants.ReservedVectorPropertyName]?[property.StorageName];

                if (node is not null)
                {
                    jsonNodeDataModel[property.StorageName] = node.DeepClone();
                }
            }
        }

        return jsonNodeDataModel.Deserialize<TRecord>(this._jsonSerializerOptions)!;
    }
}
