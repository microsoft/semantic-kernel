// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Support;

public class RedisHashSetSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => RedisTestStore.HashSetInstance;
}
