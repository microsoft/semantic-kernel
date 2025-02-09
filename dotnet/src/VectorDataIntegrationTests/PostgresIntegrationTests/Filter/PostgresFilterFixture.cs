// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace PostgresIntegrationTests.Filter;

public class PostgresFilterFixture : FilterFixtureBase<int>
{
    protected override TestStore TestStore => PostgresTestStore.Instance;
}
