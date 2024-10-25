// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

[Collection("MongoDBVectorStoreCollection")]
public class MongoDBVectorStoreTests(MongoDBVectorStoreFixture fixture)
{
    // If null, all tests will be enabled
    private const string? SkipReason = "The tests are for manual verification.";

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var sut = new MongoDBVectorStore(fixture.MongoDatabase);

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Contains("sk-test-hotels", collectionNames);
        Assert.Contains("sk-test-contacts", collectionNames);
        Assert.Contains("sk-test-addresses", collectionNames);
    }
}
