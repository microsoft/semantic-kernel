// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson;

internal interface IMongoDBMapper<TRecord>
{
    /// <summary>
    /// Maps from the consumer record data model to the storage model.
    /// </summary>
    BsonDocument MapFromDataToStorageModel(TRecord dataModel, Embedding?[]? generatedEmbeddings);

    /// <summary>
    /// Maps from the storage model to the consumer record data model.
    /// </summary>
    TRecord MapFromStorageToDataModel(BsonDocument storageModel, StorageToDataModelMapperOptions options);
}
