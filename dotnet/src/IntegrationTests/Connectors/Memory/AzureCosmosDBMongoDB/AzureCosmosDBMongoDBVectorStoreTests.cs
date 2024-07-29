// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBMongoDB;

[Collection("AzureCosmosDBMongoDBVectorStoreCollection")]
public class AzureCosmosDBMongoDBVectorStoreTests(ITestOutputHelper output, AzureCosmosDBMongoDBVectorStoreFixture fixture)
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
        Assert.Equal(3, collectionNames.Count);
        Assert.Contains("hotels", collectionNames);
        Assert.Contains("contacts", collectionNames);
        Assert.Contains("addresses", collectionNames);

        // Output
        output.WriteLine(string.Join(",", collectionNames));
    }
}
