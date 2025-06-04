// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Support;

public class RedisJsonFixture : VectorStoreFixture
{
    public override TestStore TestStore => RedisTestStore.JsonInstance;
}
