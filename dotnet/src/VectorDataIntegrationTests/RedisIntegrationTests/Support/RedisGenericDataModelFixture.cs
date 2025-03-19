// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Support;

public class RedisGenericDataModelFixture : GenericDataModelFixture<string>
{
    public override TestStore TestStore => RedisTestStore.JsonInstance;
}
