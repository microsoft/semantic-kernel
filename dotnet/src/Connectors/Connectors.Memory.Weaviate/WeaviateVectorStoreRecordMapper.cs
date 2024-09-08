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
            { WeaviateConstants.ReservedCollectionPropertyName, JsonValue.Create(this._collectionName) },
            { WeaviateConstants.ReservedKeyPropertyName, jsonNodeDataModel[this._keyProperty]!.DeepClone() },
            { WeaviateConstants.ReservedDataPropertyName, new JsonObject() },
            { WeaviateConstants.ReservedVectorPropertyName, new JsonObject() },
        };

        // Populate data properties.
        foreach (var property in this._dataProperties)
        {
            var node = jsonNodeDataModel[property];

            if (node is not null)
            {
                weaviateObjectModel[WeaviateConstants.ReservedDataPropertyName]![property] = node.DeepClone();
            }
        }

        // Populate vector properties.
        foreach (var property in this._vectorProperties)
        {
            var node = jsonNodeDataModel[property];

            if (node is not null)
            {
                weaviateObjectModel[WeaviateConstants.ReservedVectorPropertyName]![property] = node.DeepClone();
            }
        }

        return weaviateObjectModel;
    }

    public TRecord MapFromStorageToDataModel(JsonNode storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        // Transform Weaviate object model to data model.
        var jsonNodeDataModel = new JsonObject
        {
            { this._keyProperty, storageModel[WeaviateConstants.ReservedKeyPropertyName]?.DeepClone() },
        };

        // Populate data properties.
        foreach (var property in this._dataProperties)
        {
            var node = storageModel[WeaviateConstants.ReservedDataPropertyName]?[property];

            if (node is not null)
            {
                jsonNodeDataModel[property] = node.DeepClone();
            }
        }

        // Populate vector properties.
        if (options.IncludeVectors)
        {
            foreach (var property in this._vectorProperties)
            {
                var node = storageModel[WeaviateConstants.ReservedVectorPropertyName]?[property];

                if (node is not null)
                {
                    jsonNodeDataModel[property] = node.DeepClone();
                }
            }
        }

        return jsonNodeDataModel.Deserialize<TRecord>(this._jsonSerializerOptions)!;
    }
}
