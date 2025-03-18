// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Support;

public class RedisFixture : VectorStoreFixture
{
    public override TestStore TestStore => RedisTestStore.JsonInstance;
}
