// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson.Serialization.Conventions;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

[ExcludeFromCodeCoverage]
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
internal sealed class MongoDBVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, BsonDocument>
#pragma warning restore CS0618
{
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

    public BsonDocument MapFromDataToStorageModel(TRecord dataModel)
    {
        var document = dataModel.ToBsonDocument();

        // Handle key property mapping due to reserved key name in Mongo.
        if (!document.Contains(MongoDBConstants.MongoReservedKeyPropertyName))
        {
            var value = document[this._keyPropertyModelName];

            document.Remove(this._keyPropertyModelName);

            document[MongoDBConstants.MongoReservedKeyPropertyName] = value;
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

        return BsonSerializer.Deserialize<TRecord>(storageModel);
    }
}
