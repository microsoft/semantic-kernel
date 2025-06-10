// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Redis.ConformanceTests.Support;

public class RedisHashSetDynamicDataModelFixture : DynamicDataModelFixture<string>
{
    public override TestStore TestStore => RedisTestStore.HashSetInstance;
}
