// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBMongoDB;

[Collection("AzureCosmosDBMongoDBVectorStoreCollection")]
public class AzureCosmosDBMongoDBVectorStoreTests(AzureCosmosDBMongoDBVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, AzureCosmosDBMongoDBHotel>(new AzureCosmosDBMongoDBVectorStore(fixture.MongoDatabase))
{
    private const string? SkipReason = "Azure CosmosDB MongoDB cluster is required";

    [Fact(Skip = SkipReason)]
    public override async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        await base.ItCanGetAListOfExistingCollectionNamesAsync();
    }
}
