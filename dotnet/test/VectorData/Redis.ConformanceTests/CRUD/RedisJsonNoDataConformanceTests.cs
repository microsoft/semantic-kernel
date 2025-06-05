// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Redis.ConformanceTests.CRUD;

public class RedisJsonNoDataConformanceTests(RedisJsonNoDataConformanceTests.Fixture fixture)
    : NoDataConformanceTests<string>(fixture), IClassFixture<RedisJsonNoDataConformanceTests.Fixture>
{
    public new class Fixture : NoDataConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;
    }
}
