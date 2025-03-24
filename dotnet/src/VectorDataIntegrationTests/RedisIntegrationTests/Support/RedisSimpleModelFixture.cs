// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Support;

public class RedisSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => RedisTestStore.JsonInstance;
}
