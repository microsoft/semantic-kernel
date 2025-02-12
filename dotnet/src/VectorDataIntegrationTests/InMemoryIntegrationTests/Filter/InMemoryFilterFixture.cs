// Copyright (c) Microsoft. All rights reserved.

using InMemoryIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace PostgresIntegrationTests.Filter;

public class InMemoryFilterFixture : FilterFixtureBase<int>
{
    protected override TestStore TestStore => InMemoryTestStore.Instance;
}
