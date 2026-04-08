// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Redis.ConformanceTests.ModelTests;

public class RedisJsonNoDataModelTests(RedisJsonNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<RedisJsonNoDataModelTests.Fixture>
{
    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;
    }
}
