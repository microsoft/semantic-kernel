// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Redis.ConformanceTests.Support;

public class RedisJsonFixture : VectorStoreFixture
{
    public override TestStore TestStore => RedisTestStore.JsonInstance;
}
