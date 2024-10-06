// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

<<<<<<< Updated upstream
internal sealed class WeaviateVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, JsonNode> where TRecord : class
=======
<<<<<<< HEAD
internal sealed class WeaviateVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, JsonNode> where TRecord : class
=======
internal sealed class WeaviateVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, JsonObject> where TRecord : class
>>>>>>> main
>>>>>>> Stashed changes
{
    private readonly string _collectionName;

    private readonly string _keyProperty;

<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
    private readonly List<string> _dataProperties;

    private readonly List<string> _vectorProperties;

    private readonly Dictionary<string, string> _storagePropertyNames;
<<<<<<< Updated upstream
=======
=======
    private readonly IReadOnlyList<string> _dataProperties;

    private readonly IReadOnlyList<string> _vectorProperties;

    private readonly IReadOnlyDictionary<string, string> _storagePropertyNames;
>>>>>>> main
>>>>>>> Stashed changes

    private readonly JsonSerializerOptions _jsonSerializerOptions;

    public WeaviateVectorStoreRecordMapper(
        string collectionName,
        VectorStoreRecordKeyProperty keyProperty,
<<<<<<< Updated upstream
        List<VectorStoreRecordDataProperty> dataProperties,
        List<VectorStoreRecordVectorProperty> vectorProperties,
        Dictionary<string, string> storagePropertyNames,
=======
<<<<<<< HEAD
        List<VectorStoreRecordDataProperty> dataProperties,
        List<VectorStoreRecordVectorProperty> vectorProperties,
        Dictionary<string, string> storagePropertyNames,
=======
        IReadOnlyList<VectorStoreRecordDataProperty> dataProperties,
        IReadOnlyList<VectorStoreRecordVectorProperty> vectorProperties,
        IReadOnlyDictionary<string, string> storagePropertyNames,
>>>>>>> main
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
    public JsonNode MapFromDataToStorageModel(TRecord dataModel)
=======
<<<<<<< HEAD
    public JsonNode MapFromDataToStorageModel(TRecord dataModel)
=======
    public JsonObject MapFromDataToStorageModel(TRecord dataModel)
>>>>>>> main
>>>>>>> Stashed changes
    {
        Verify.NotNull(dataModel);

        var jsonNodeDataModel = JsonSerializer.SerializeToNode(dataModel, this._jsonSerializerOptions)!;

        // Transform data model to Weaviate object model.
        var weaviateObjectModel = new JsonObject
        {
<<<<<<< Updated upstream
            { WeaviateConstants.ReservedCollectionPropertyName, JsonValue.Create(this._collectionName) },
=======
<<<<<<< HEAD
            { WeaviateConstants.ReservedCollectionPropertyName, JsonValue.Create(this._collectionName) },
=======
            { WeaviateConstants.CollectionPropertyName, JsonValue.Create(this._collectionName) },
>>>>>>> main
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
    public TRecord MapFromStorageToDataModel(JsonNode storageModel, StorageToDataModelMapperOptions options)
=======
<<<<<<< HEAD
    public TRecord MapFromStorageToDataModel(JsonNode storageModel, StorageToDataModelMapperOptions options)
=======
    public TRecord MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
>>>>>>> main
>>>>>>> Stashed changes
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
