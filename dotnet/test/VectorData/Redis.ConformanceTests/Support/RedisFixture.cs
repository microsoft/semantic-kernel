// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Redis.ConformanceTests.Support;

public class RedisFixture : VectorStoreFixture
{
    public override TestStore TestStore => RedisTestStore.JsonInstance;
}
