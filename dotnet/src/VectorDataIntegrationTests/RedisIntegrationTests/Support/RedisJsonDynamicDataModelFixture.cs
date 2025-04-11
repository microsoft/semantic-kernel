// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Support;

public class RedisJsonDynamicDataModelFixture : DynamicDataModelFixture<string>
{
    public override TestStore TestStore => RedisTestStore.JsonInstance;
}
