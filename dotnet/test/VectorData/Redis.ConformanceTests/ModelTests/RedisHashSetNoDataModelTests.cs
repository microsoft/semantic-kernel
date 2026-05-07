// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Redis.ConformanceTests.ModelTests;

public class RedisHashSetNoDataModelTests(RedisHashSetNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<RedisHashSetNoDataModelTests.Fixture>
{
    public override async Task GetAsync_single_record(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var received = await this.Collection.GetAsync(expectedRecord.Key, new() { IncludeVectors = includeVectors });

        if (includeVectors)
        {
            expectedRecord.AssertEqual(received, includeVectors, fixture.TestStore.VectorsComparable);
        }
        else
        {
            // When vectors aren't included and there's no other data, we get null back.
            Assert.Null(received);
        }
    }

    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;
    }
}
