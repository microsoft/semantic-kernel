// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace SqlServerIntegrationTests.CRUD;

public class SqlServerNoDataConformanceTests(SqlServerNoDataConformanceTests.Fixture fixture)
    : NoDataConformanceTests<string>(fixture), IClassFixture<SqlServerNoDataConformanceTests.Fixture>
{
    public new class Fixture : NoDataConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
