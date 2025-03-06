// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IKeywordHybridSearch{TRecord}"/>.
/// </summary>
/// <param name="fixture">Azure Cosmos DB MongoDB setup and teardown.</param>
[Collection("AzureCosmosDBMongoDBVectorStoreCollection")]
public class AzureCosmosDBMongoDBKeywordVectorizedHybridSearchTests(AzureCosmosDBMongoDBVectorStoreFixture fixture) : BaseKeywordVectorizedHybridSearchTests<string>
{
    protected override string Key1 => "1";
    protected override string Key2 => "2";
    protected override string Key3 => "3";
    protected override string Key4 => "4";
    protected override int DelayAfterUploadInMilliseconds => 2000;

    protected override IVectorStoreRecordCollection<string, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        return new AzureCosmosDBMongoDBVectorStoreRecordCollection<TRecord>(fixture.MongoDatabase, recordCollectionName + AzureCosmosDBMongoDBVectorStoreFixture.TestIndexPostfix, new()
        {
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }
}
