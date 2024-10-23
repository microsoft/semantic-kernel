// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson.Serialization.Conventions;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

[ExcludeFromCodeCoverage]
internal sealed class MongoDBVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, BsonDocument>
{
    /// <summary>A key property info of the data model.</summary>
    private readonly PropertyInfo _keyProperty;

    /// <summary>A key property name of the data model.</summary>
    private readonly string _keyPropertyName;

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBVectorStoreRecordMapper{TRecord}"/> class.
    /// </summary>
    /// <param name="propertyReader">A helper to access property information for the current data model and record definition.</param>
    public MongoDBVectorStoreRecordMapper(VectorStoreRecordPropertyReader propertyReader)
    {
        propertyReader.VerifyKeyProperties(MongoDBConstants.SupportedKeyTypes);
        propertyReader.VerifyDataProperties(MongoDBConstants.SupportedDataTypes, supportEnumerable: true);
        propertyReader.VerifyVectorProperties(MongoDBConstants.SupportedVectorTypes);

        this._keyPropertyName = propertyReader.KeyPropertyName;
        this._keyProperty = propertyReader.KeyPropertyInfo;

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
            var value = document[this._keyPropertyName];

            document.Remove(this._keyPropertyName);

            document[MongoDBConstants.MongoReservedKeyPropertyName] = value;
        }

        return document;
    }

    public TRecord MapFromStorageToDataModel(BsonDocument storageModel, StorageToDataModelMapperOptions options)
    {
        // Handle key property mapping due to reserved key name in Mongo.
        if (!this._keyPropertyName.Equals(MongoDBConstants.DataModelReservedKeyPropertyName, StringComparison.OrdinalIgnoreCase) &&
            this._keyProperty.GetCustomAttribute<BsonIdAttribute>() is null)
        {
            var value = storageModel[MongoDBConstants.MongoReservedKeyPropertyName];

            storageModel.Remove(MongoDBConstants.MongoReservedKeyPropertyName);

            storageModel[this._keyPropertyName] = value;
        }

        return BsonSerializer.Deserialize<TRecord>(storageModel);
    }
}
