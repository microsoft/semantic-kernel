// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Redis.ConformanceTests.ModelTests;

public class RedisJsonNoVectorModelTests(RedisJsonNoVectorModelTests.Fixture fixture)
    : NoVectorModelTests<string>(fixture), IClassFixture<RedisJsonNoVectorModelTests.Fixture>
{
    public new class Fixture : NoVectorModelTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;
    }
}
