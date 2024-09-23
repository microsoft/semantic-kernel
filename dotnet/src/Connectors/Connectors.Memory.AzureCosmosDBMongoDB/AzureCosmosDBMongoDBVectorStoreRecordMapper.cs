// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
<<<<<<< HEAD
using System.Reflection;
using Microsoft.SemanticKernel.Data;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Bson.Serialization.Attributes;
=======
using Microsoft.SemanticKernel.Data;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
using MongoDB.Bson.Serialization.Conventions;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

internal sealed class AzureCosmosDBMongoDBVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, BsonDocument>
    where TRecord : class
{
    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(string)
    ];

    /// <summary>A set of types that data properties on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(bool),
        typeof(bool?),
        typeof(string),
        typeof(int),
        typeof(int?),
        typeof(long),
        typeof(long?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
        typeof(ReadOnlyMemory<double>),
        typeof(ReadOnlyMemory<double>?)
    ];

<<<<<<< HEAD
    /// <summary>A key property info of the data model.</summary>
    private readonly PropertyInfo _keyProperty;

    /// <summary>A key property name of the data model.</summary>
    private readonly string _keyPropertyName;
=======
    /// <summary>A dictionary that maps from a property name to the storage name.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames;
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureCosmosDBMongoDBVectorStoreRecordMapper{TRecord}"/> class.
    /// </summary>
    /// <param name="vectorStoreRecordDefinition">The record definition that defines the schema of the record type.</param>
<<<<<<< HEAD
    /// <param name="keyPropertyName">A key property name of the data model.</param>
    public AzureCosmosDBMongoDBVectorStoreRecordMapper(VectorStoreRecordDefinition vectorStoreRecordDefinition, string keyPropertyName)
=======
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the configured name that should be used when storing it.</param>
    public AzureCosmosDBMongoDBVectorStoreRecordMapper(VectorStoreRecordDefinition vectorStoreRecordDefinition, Dictionary<string, string> storagePropertyNames)
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
    {
        var (keyProperty, dataProperties, vectorProperties) = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), vectorStoreRecordDefinition, supportsMultipleVectors: true);

        VectorStoreRecordPropertyReader.VerifyPropertyTypes([keyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(dataProperties, s_supportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(vectorProperties, s_supportedVectorTypes, "Vector");

<<<<<<< HEAD
        this._keyPropertyName = keyPropertyName;
        this._keyProperty = keyProperty;

        var conventionPack = new ConventionPack
        {
            new IgnoreExtraElementsConvention(ignoreExtraElements: true)
=======
        this._storagePropertyNames = storagePropertyNames;

        // Use Mongo reserved key property name as storage key property name
        this._storagePropertyNames[keyProperty.Name] = AzureCosmosDBMongoDBConstants.MongoReservedKeyPropertyName;

        var conventionPack = new ConventionPack
        {
            new IgnoreExtraElementsConvention(ignoreExtraElements: true),
            new AzureCosmosDBMongoDBNamingConvention(this._storagePropertyNames)
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
        };

        ConventionRegistry.Register(
            nameof(AzureCosmosDBMongoDBVectorStoreRecordMapper<TRecord>),
            conventionPack,
            type => type == typeof(TRecord));
    }

    public BsonDocument MapFromDataToStorageModel(TRecord dataModel)
<<<<<<< HEAD
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
=======
        => dataModel.ToBsonDocument();

    public TRecord MapFromStorageToDataModel(BsonDocument storageModel, StorageToDataModelMapperOptions options)
        => BsonSerializer.Deserialize<TRecord>(storageModel);
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
}
