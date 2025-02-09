// Copyright (c) Microsoft. All rights reserved.

using MongoDB.Driver;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace MongoDBIntegrationTests.Filter;

public class CosmosMongoFiltersNotSupported(CosmosMongoFilterFixture fixture) : IClassFixture<CosmosMongoFilterFixture>
{
    [ConditionalFact]
    public virtual async Task Equal_with_int()
    {
        // Cosmos MongoDB vCore doesn't yet support filters with vector search:
        // Command aggregate failed: $filter is not supported for vector search yet..
        await Assert.ThrowsAsync<MongoCommandException>(() => fixture.Collection.VectorizedSearchAsync(
            new ReadOnlyMemory<float>([1, 2, 3]),
            new()
            {
                NewFilter = r => r.Int == 8,
                Top = fixture.TestData.Count
            }));
    }
}
