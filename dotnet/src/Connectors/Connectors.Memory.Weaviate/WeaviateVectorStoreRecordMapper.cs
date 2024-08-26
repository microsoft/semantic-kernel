// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, JsonNode> where TRecord : class
{
    private readonly string _collectionName;

    private readonly string _keyProperty;

    private readonly List<string> _dataProperties;

    private readonly List<string> _vectorProperties;

    private readonly Dictionary<string, string> _storagePropertyNames;

    private readonly JsonSerializerOptions _jsonSerializerOptions;

    public WeaviateVectorStoreRecordMapper(
        string collectionName,
        VectorStoreRecordKeyProperty keyProperty,
        List<VectorStoreRecordDataProperty> dataProperties,
        List<VectorStoreRecordVectorProperty> vectorProperties,
        Dictionary<string, string> storagePropertyNames,
        JsonSerializerOptions jsonSerializerOptions)
    {
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(keyProperty);
        Verify.NotNull(dataProperties);
        Verify.NotNull(vectorProperties);
        Verify.NotNull(storagePropertyNames);
        Verify.NotNull(jsonSerializerOptions);

        this._collectionName = collectionName;
        this._storagePropertyNames = storagePropertyNames;
        this._jsonSerializerOptions = jsonSerializerOptions;

        this._keyProperty = this._storagePropertyNames[keyProperty.DataModelPropertyName];
        this._dataProperties = dataProperties.Select(property => this._storagePropertyNames[property.DataModelPropertyName]).ToList();
        this._vectorProperties = vectorProperties.Select(property => this._storagePropertyNames[property.DataModelPropertyName]).ToList();
    }

    public JsonNode MapFromDataToStorageModel(TRecord dataModel)
    {
        Verify.NotNull(dataModel);

        var jsonNodeDataModel = JsonSerializer.SerializeToNode(dataModel, this._jsonSerializerOptions)!;

        // Transform data model to Weaviate object model.
        var weaviateObjectModel = new JsonObject
        {
            { WeaviateConstants.ReservedKeyPropertyName, jsonNodeDataModel[this._keyProperty] },
            { WeaviateConstants.ReservedDataPropertyName, new JsonObject() },
            { WeaviateConstants.ReservedVectorPropertyName, new JsonObject() },
        };

        // Populate data properties.
        foreach (var property in this._dataProperties)
        {
            weaviateObjectModel[WeaviateConstants.ReservedDataPropertyName]![property] = jsonNodeDataModel[property];
        }

        // Populate vector properties.
        foreach (var property in this._vectorProperties)
        {
            weaviateObjectModel[WeaviateConstants.ReservedVectorPropertyName]![property] = jsonNodeDataModel[property];
        }

        return weaviateObjectModel;
    }

    public TRecord MapFromStorageToDataModel(JsonNode storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        // Transform Weaviate object model to data model.
        var jsonNodeDataModel = new JsonObject
        {
            { this._keyProperty, storageModel[WeaviateConstants.ReservedKeyPropertyName] },
        };

        // Populate data properties.
        foreach (var property in this._dataProperties)
        {
            jsonNodeDataModel[property] = storageModel[WeaviateConstants.ReservedDataPropertyName]![property];
        }

        // Populate vector properties.
        foreach (var property in this._vectorProperties)
        {
            jsonNodeDataModel[property] = storageModel[WeaviateConstants.ReservedVectorPropertyName]![property];
        }

        return jsonNodeDataModel.Deserialize<TRecord>(this._jsonSerializerOptions)!;
    }
}
