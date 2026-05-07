// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Redis.ConformanceTests.ModelTests;

public class RedisHashSetDynamicModelTests(RedisHashSetDynamicModelTests.Fixture fixture)
    : DynamicModelTests<string>(fixture), IClassFixture<RedisHashSetDynamicModelTests.Fixture>
{
    public override async Task GetAsync_with_filter_and_multiple_OrderBys()
    {
        var exception = await Assert.ThrowsAsync<NotSupportedException>(base.GetAsync_with_filter_and_multiple_OrderBys);

        Assert.Equal("Redis does not support ordering by more than one property.", exception.Message);
    }

    public new class Fixture : DynamicModelTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;
    }
}
