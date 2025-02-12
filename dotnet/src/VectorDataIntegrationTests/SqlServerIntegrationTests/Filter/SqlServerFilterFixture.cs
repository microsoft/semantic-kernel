// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Filter;

public class SqlServerFilterFixture : FilterFixtureBase<string>
{
    protected override TestStore TestStore => SqlServerTestStore.Instance;
}
