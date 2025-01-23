// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Filter;

public class RedisFilterFixture : FilterFixtureBase<string>
{
    protected override TestStore TestStore => RedisTestStore.Instance;

    // Override to remove the bool property, which isn't (currently) supported on Redis
    protected override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties = base.GetRecordDefinition().Properties.Where(p => p.PropertyType != typeof(bool)).ToList()
        };
}
