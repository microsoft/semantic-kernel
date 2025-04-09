// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBMongoDB;

[Collection("AzureCosmosDBMongoDBVectorStoreCollection")]
[DisableVectorStoreTests(Skip = "Azure CosmosDB MongoDB cluster is required")]
public class AzureCosmosDBMongoDBVectorStoreTests(AzureCosmosDBMongoDBVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, AzureCosmosDBMongoDBHotel>(new AzureCosmosDBMongoDBVectorStore(fixture.MongoDatabase))
{
}
