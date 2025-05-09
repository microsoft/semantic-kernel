// Copyright (c) Microsoft. All rights reserved.

using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace SqliteIntegrationTests.CRUD;

public class SqliteNoDataConformanceTests(SqliteNoDataConformanceTests.Fixture fixture)
    : NoDataConformanceTests<string>(fixture), IClassFixture<SqliteNoDataConformanceTests.Fixture>
{
    public new class Fixture : NoDataConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;
    }
}
