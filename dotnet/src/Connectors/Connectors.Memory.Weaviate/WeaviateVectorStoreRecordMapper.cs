// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateVectorStoreRecordMapper<TRecord> : IWeaviateMapper<TRecord>
{
    private readonly string _collectionName;
    private readonly bool _hasNamedVectors;
    private readonly VectorStoreRecordModel _model;
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    private readonly string _vectorPropertyName;

    public WeaviateVectorStoreRecordMapper(
        string collectionName,
        bool hasNamedVectors,
        VectorStoreRecordModel model,
        JsonSerializerOptions jsonSerializerOptions)
    {
        this._collectionName = collectionName;
        this._hasNamedVectors = hasNamedVectors;
        this._model = model;
        this._jsonSerializerOptions = jsonSerializerOptions;

        this._vectorPropertyName = hasNamedVectors ?
            WeaviateConstants.ReservedVectorPropertyName :
            WeaviateConstants.ReservedSingleVectorPropertyName;
    }

    public JsonObject MapFromDataToStorageModel(TRecord dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
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
            { this._vectorPropertyName, new JsonObject() },
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
        if (this._hasNamedVectors)
        {
            for (var i = 0; i < this._model.VectorProperties.Count; i++)
            {
                var property = this._model.VectorProperties[i];

                if (generatedEmbeddings?[i] is IReadOnlyList<Embedding> e)
                {
                    weaviateObjectModel[this._vectorPropertyName]![property.StorageName] = e[recordIndex] switch
                    {
                        Embedding<float> fe => JsonValue.Create(fe.Vector.ToArray()),
                        Embedding<double> de => JsonValue.Create(de.Vector.ToArray()),
                        _ => throw new UnreachableException()
                    };
                }
                else
                {
                    var node = jsonNodeDataModel[property.StorageName];

                    if (node is not null)
                    {
                        weaviateObjectModel[this._vectorPropertyName]![property.StorageName] = node.DeepClone();
                    }
                }
            }
        }
        else
        {
            var property = this._model.VectorProperty;

            if (generatedEmbeddings?.Single() is IReadOnlyList<Embedding> e)
            {
                weaviateObjectModel[this._vectorPropertyName] = e[recordIndex] switch
                {
                    Embedding<float> fe => JsonValue.Create(fe.Vector.ToArray()),
                    Embedding<double> de => JsonValue.Create(de.Vector.ToArray()),
                    _ => throw new UnreachableException()
                };
            }
            else
            {
                var node = jsonNodeDataModel[property.StorageName];

                if (node is not null)
                {
                    weaviateObjectModel[this._vectorPropertyName] = node.DeepClone();
                }
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
            if (this._hasNamedVectors)
            {
                foreach (var property in this._model.VectorProperties)
                {
                    var node = storageModel[this._vectorPropertyName]?[property.StorageName];

                    if (node is not null)
                    {
                        jsonNodeDataModel[property.StorageName] = node.DeepClone();
                    }
                }
            }
            else
            {
                var vectorProperty = this._model.VectorProperty;
                var node = storageModel[this._vectorPropertyName];

                if (node is not null)
                {
                    jsonNodeDataModel[vectorProperty.StorageName] = node.DeepClone();
                }
            }
        }

        return jsonNodeDataModel.Deserialize<TRecord>(this._jsonSerializerOptions)!;
    }
}
