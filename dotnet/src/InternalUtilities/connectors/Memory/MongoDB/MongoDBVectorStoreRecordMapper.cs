// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson.Serialization.Conventions;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

[ExcludeFromCodeCoverage]
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
internal sealed class MongoDBVectorStoreRecordMapper<TRecord> : IMongoDBMapper<TRecord>
#pragma warning restore CS0618
{
    private readonly VectorStoreRecordModel _model;

    /// <summary>A key property info of the data model.</summary>
    private readonly PropertyInfo? _keyClrProperty;

    /// <summary>A key property name of the data model.</summary>
    private readonly string _keyPropertyModelName;

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBVectorStoreRecordMapper{TRecord}"/> class.
    /// </summary>
    /// <param name="model">The model.</param>
    public MongoDBVectorStoreRecordMapper(VectorStoreRecordModel model)
    {
        this._model = model;

        var keyProperty = model.KeyProperty;
        this._keyPropertyModelName = keyProperty.ModelName;
        this._keyClrProperty = keyProperty.PropertyInfo;

        var conventionPack = new ConventionPack
        {
            new IgnoreExtraElementsConvention(ignoreExtraElements: true)
        };

        ConventionRegistry.Register(
            nameof(MongoDBVectorStoreRecordMapper<TRecord>),
            conventionPack,
            type => type == typeof(TRecord));
    }

    public BsonDocument MapFromDataToStorageModel(TRecord dataModel, Embedding?[]? generatedEmbeddings)
    {
        var document = dataModel.ToBsonDocument();

        // Handle key property mapping due to reserved key name in Mongo.
        if (!document.Contains(MongoDBConstants.MongoReservedKeyPropertyName))
        {
            var value = document[this._keyPropertyModelName];

            document.Remove(this._keyPropertyModelName);

            document[MongoDBConstants.MongoReservedKeyPropertyName] = value;
        }

        // Go over the vector properties; those which have an embedding generator configured on them will have embedding generators, overwrite
        // the value in the JSON object with that.
        if (generatedEmbeddings is not null)
        {
            for (var i = 0; i < this._model.VectorProperties.Count; i++)
            {
                if (generatedEmbeddings[i] is not null)
                {
                    var property = this._model.VectorProperties[i];
                    Debug.Assert(property.EmbeddingGenerator is not null);
                    var embedding = generatedEmbeddings[i];
                    document[property.StorageName] = embedding switch
                    {
                        Embedding<float> e => BsonArray.Create(e.Vector.ToArray()),
                        Embedding<double> e => BsonArray.Create(e.Vector.ToArray()),
                        _ => throw new UnreachableException()
                    };
                }
            }
        }

        return document;
    }

    public TRecord MapFromStorageToDataModel(BsonDocument storageModel, StorageToDataModelMapperOptions options)
    {
        // Handle key property mapping due to reserved key name in Mongo.
        if (!this._keyPropertyModelName.Equals(MongoDBConstants.DataModelReservedKeyPropertyName, StringComparison.OrdinalIgnoreCase) &&
            this._keyClrProperty?.GetCustomAttribute<BsonIdAttribute>() is null)
        {
            var value = storageModel[MongoDBConstants.MongoReservedKeyPropertyName];

            storageModel.Remove(MongoDBConstants.MongoReservedKeyPropertyName);

            storageModel[this._keyPropertyModelName] = value;
        }

        // For vector properties which have embedding generation configured, we need to remove the embeddings before deserializing
        // (we can't go back from an embedding to e.g. string).
        // For other cases (no embedding generation), we leave the properties even if IncludeVectors is false.
        if (!options.IncludeVectors)
        {
            foreach (var vectorProperty in this._model.VectorProperties)
            {
                if (vectorProperty.EmbeddingGenerator is not null)
                {
                    storageModel.Remove(vectorProperty.StorageName);
                }
            }
        }

        return BsonSerializer.Deserialize<TRecord>(storageModel);
    }
}
