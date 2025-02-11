// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSQLIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace CosmosNoSQLIntegrationTests.Filter;

public class CosmosNoSQLFilterFixture : FilterFixtureBase<string>
{
    protected override TestStore TestStore => CosmosNoSqlTestStore.Instance;
}
