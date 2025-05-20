// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.PgVector;

[Collection("PostgresVectorStoreCollection")]
public class PostgresVectorStoreTests(PostgresVectorStoreFixture fixture)
{
    [Fact]
    public async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var sut = fixture.VectorStore;

        // Setup
        var collection = sut.GetCollection<long, PostgresHotel<long>>("VS_TEST_HOTELS");
        await collection.EnsureCollectionExistsAsync();

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Contains("VS_TEST_HOTELS", collectionNames);
    }
}
