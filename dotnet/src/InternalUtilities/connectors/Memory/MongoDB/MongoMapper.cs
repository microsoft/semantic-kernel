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
    where TRecord : class
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
        for (var i = 0; i < this._model.VectorProperties.Count; i++)
        {
            var property = this._model.VectorProperties[i];

            Embedding<float>? embedding = generatedEmbeddings?[i]?[recordIndex] is Embedding e ? (Embedding<float>)e : null;

            if (embedding is null)
            {
                switch (Nullable.GetUnderlyingType(property.Type) ?? property.Type)
                {
                    case var t when t == typeof(ReadOnlyMemory<float>):
                    case var t2 when t2 == typeof(float[]):
                        // The .NET vector property is a ReadOnlyMemory<float> or float[] (not an Embedding<float>), which means that ToBsonDocument()
                        // already serialized it correctly above.
                        // In addition, there's no generated embedding (which would be an Embedding<float> which we'd need to handle manually).
                        // So there's nothing for us to do.
                        continue;

                    case var t when t == typeof(Embedding<float>):
                        embedding = (Embedding<float>)property.GetValueAsObject(dataModel)!;
                        break;

                    default:
                        throw new UnreachableException();
                }
            }

            document[property.StorageName] = BsonArray.Create(embedding.Vector.ToArray());
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

        if (includeVectors)
        {
            foreach (var vectorProperty in this._model.VectorProperties)
            {
                // If the vector property .NET type is Embedding<float>, we need to create the BSON structure for it
                // (BSON array embedded inside an object representing the embedding), so that the deserialization below
                // works correctly.
                if (vectorProperty.Type == typeof(Embedding<float>))
                {
                    storageModel[vectorProperty.StorageName] = new BsonDocument
                    {
                        [nameof(Embedding<float>.Vector)] = BsonArray.Create(storageModel[vectorProperty.StorageName])
                    };
                }
            }
        }
        else
        {
            // If includeVectors is false, remove the values; this allows us to not project them out of Mongo in the future
            // (more efficient) without introducing a breaking change.
            foreach (var vectorProperty in this._model.VectorProperties)
            {
                storageModel.Remove(vectorProperty.StorageName);
            }
        }

        return BsonSerializer.Deserialize<TRecord>(storageModel);
    }
}
