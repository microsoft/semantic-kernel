// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson.Serialization.Conventions;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

[ExcludeFromCodeCoverage]
internal sealed class MongoMapper<TRecord> : IMongoMapper<TRecord>
{
    private readonly CollectionModel _model;

    /// <summary>A key property info of the data model.</summary>
    private readonly PropertyInfo? _keyClrProperty;

    /// <summary>A key property name of the data model.</summary>
    private readonly string _keyPropertyModelName;

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoMapper{TRecord}"/> class.
    /// </summary>
    /// <param name="model">The model.</param>
    public MongoMapper(CollectionModel model)
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
            nameof(MongoMapper<TRecord>),
            conventionPack,
            type => type == typeof(TRecord));
    }

    public BsonDocument MapFromDataToStorageModel(TRecord dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        var document = dataModel.ToBsonDocument();

        // Handle key property mapping due to reserved key name in Mongo.
        if (!document.Contains(MongoConstants.MongoReservedKeyPropertyName))
        {
            var value = document[this._keyPropertyModelName];

            document.Remove(this._keyPropertyModelName);

            document[MongoConstants.MongoReservedKeyPropertyName] = value;
        }

        // Go over the vector properties; those which have an embedding generator configured on them will have embedding generators, overwrite
        // the value in the JSON object with that.
        if (generatedEmbeddings is not null)
        {
            for (var i = 0; i < this._model.VectorProperties.Count; i++)
            {
                if (generatedEmbeddings?[i]?[recordIndex] is Embedding embedding)
                {
                    var property = this._model.VectorProperties[i];

                    Debug.Assert(property.EmbeddingGenerator is not null);

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

    public TRecord MapFromStorageToDataModel(BsonDocument storageModel, bool includeVectors)
    {
        // Handle key property mapping due to reserved key name in Mongo.
        if (!this._keyPropertyModelName.Equals(MongoConstants.DataModelReservedKeyPropertyName, StringComparison.OrdinalIgnoreCase) &&
            this._keyClrProperty?.GetCustomAttribute<BsonIdAttribute>() is null)
        {
            var value = storageModel[MongoConstants.MongoReservedKeyPropertyName];

            storageModel.Remove(MongoConstants.MongoReservedKeyPropertyName);

            storageModel[this._keyPropertyModelName] = value;
        }

        // For vector properties which have embedding generation configured, we need to remove the embeddings before deserializing
        // (we can't go back from an embedding to e.g. string).
        // For other cases (no embedding generation), we leave the properties even if IncludeVectors is false.
        if (!includeVectors)
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
