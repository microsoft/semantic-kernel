// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using Microsoft.SemanticKernel.Data;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

internal sealed class AzureCosmosDBMongoDBVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, BsonDocument>
    where TRecord : class
{
    /// <summary>A key property info of the data model.</summary>
    private readonly PropertyInfo _keyProperty;

    /// <summary>A key property name of the data model.</summary>
    private readonly string _keyPropertyName;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureCosmosDBMongoDBVectorStoreRecordMapper{TRecord}"/> class.
    /// </summary>
    /// <param name="vectorStoreRecordDefinition">The record definition that defines the schema of the record type.</param>
    /// <param name="keyPropertyName">A key property name of the data model.</param>
    public AzureCosmosDBMongoDBVectorStoreRecordMapper(VectorStoreRecordDefinition vectorStoreRecordDefinition, string keyPropertyName)
    {
        var (keyProperty, dataProperties, vectorProperties) = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), vectorStoreRecordDefinition, supportsMultipleVectors: true);

        VectorStoreRecordPropertyReader.VerifyPropertyTypes([keyProperty], AzureCosmosDBMongoDBConstants.SupportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(dataProperties, AzureCosmosDBMongoDBConstants.SupportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(vectorProperties, AzureCosmosDBMongoDBConstants.SupportedVectorTypes, "Vector");

        this._keyPropertyName = keyPropertyName;
        this._keyProperty = keyProperty;
    }

    public BsonDocument MapFromDataToStorageModel(TRecord dataModel)
    {
        var document = dataModel.ToBsonDocument();

        // Handle key property mapping due to reserved key name in Mongo.
        if (!document.Contains(AzureCosmosDBMongoDBConstants.MongoReservedKeyPropertyName))
        {
            var value = document[this._keyPropertyName];

            document.Remove(this._keyPropertyName);

            document[AzureCosmosDBMongoDBConstants.MongoReservedKeyPropertyName] = value;
        }

        return document;
    }

    public TRecord MapFromStorageToDataModel(BsonDocument storageModel, StorageToDataModelMapperOptions options)
    {
        // Handle key property mapping due to reserved key name in Mongo.
        if (!this._keyPropertyName.Equals(AzureCosmosDBMongoDBConstants.DataModelReservedKeyPropertyName, StringComparison.OrdinalIgnoreCase) &&
            this._keyProperty.GetCustomAttribute<BsonIdAttribute>() is null)
        {
            var value = storageModel[AzureCosmosDBMongoDBConstants.MongoReservedKeyPropertyName];

            storageModel.Remove(AzureCosmosDBMongoDBConstants.MongoReservedKeyPropertyName);

            storageModel[this._keyPropertyName] = value;
        }

        return BsonSerializer.Deserialize<TRecord>(storageModel);
    }
}
