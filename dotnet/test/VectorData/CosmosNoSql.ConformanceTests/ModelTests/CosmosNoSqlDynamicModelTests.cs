// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests.ModelTests;

public class CosmosNoSqlDynamicModelTests(CosmosNoSqlDynamicModelTests.Fixture fixture)
    : DynamicModelTests<string>(fixture), IClassFixture<CosmosNoSqlDynamicModelTests.Fixture>
{
    public override async Task GetAsync_with_filter_and_multiple_OrderBys()
    {
        // CosmosException: The order by query does not have a corresponding composite index that it can be served from.
        var exception = await Assert.ThrowsAsync<VectorStoreException>(base.GetAsync_with_filter_and_multiple_OrderBys);
        Assert.IsType<CosmosException>(exception.InnerException);
    }

    public new class Fixture : DynamicModelTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
