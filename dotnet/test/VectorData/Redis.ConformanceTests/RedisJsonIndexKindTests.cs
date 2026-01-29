// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Redis.ConformanceTests;

public class RedisJsonIndexKindTests(RedisJsonIndexKindTests.Fixture fixture)
    : IndexKindTests<string>(fixture), IClassFixture<RedisJsonIndexKindTests.Fixture>
{
    public new class Fixture() : IndexKindTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;
    }
}
