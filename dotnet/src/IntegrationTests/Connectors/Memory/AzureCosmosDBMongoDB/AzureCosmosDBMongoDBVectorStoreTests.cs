// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBMongoDB;

[Collection("AzureCosmosDBMongoDBVectorStoreCollection")]
public class AzureCosmosDBMongoDBVectorStoreTests(AzureCosmosDBMongoDBVectorStoreFixture fixture)
{
    private const string? SkipReason = "Azure CosmosDB MongoDB cluster is required";

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var sut = new AzureCosmosDBMongoDBVectorStore(fixture.MongoDatabase);

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Contains("sk-test-hotels", collectionNames);
        Assert.Contains("sk-test-contacts", collectionNames);
        Assert.Contains("sk-test-addresses", collectionNames);
    }
}
