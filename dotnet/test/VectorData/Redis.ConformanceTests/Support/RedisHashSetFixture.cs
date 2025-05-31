// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Support;

public class RedisHashSetFixture : VectorStoreFixture
{
    public override TestStore TestStore => RedisTestStore.HashSetInstance;
}
