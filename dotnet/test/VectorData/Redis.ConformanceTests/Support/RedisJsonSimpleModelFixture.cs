// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Redis.ConformanceTests.Support;

public class RedisJsonSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => RedisTestStore.JsonInstance;
}
