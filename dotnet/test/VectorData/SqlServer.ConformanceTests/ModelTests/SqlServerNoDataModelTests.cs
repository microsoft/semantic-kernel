// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqlServer.ConformanceTests.ModelTests;

public class SqlServerNoDataModelTests(SqlServerNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<SqlServerNoDataModelTests.Fixture>
{
    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
